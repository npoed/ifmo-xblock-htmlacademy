import datetime

from webob.exc import HTTPFound
from webob import Response
from xblock.core import XBlock
from xblock.fragment import Fragment
from xblock_academy_fields import HTMLAcademyXBlockFields
from xblock_academy_resources import XBlockResources
from xmodule.util.duedate import get_extended_due_date
from lms.djangoapps.courseware.models import StudentModule
from opaque_keys.edx.keys import UsageKey
import hashlib
import json
import requests
import pytz


class HTMLAcademyXBlock(HTMLAcademyXBlockFields, XBlockResources, XBlock):

    icon_class = 'problem'
    has_score = True
    package = __package__

    # Use this unless submissions api is used
    always_recalculate_grades = True

    def student_view(self, context):

        if context is None:
            context = dict()

        context.update(self._get_student_context())

        fragment = Fragment()
        fragment.add_content(self.load_template('student_view.html', context))
        fragment.add_javascript(self.load_js('student_view.js'))
        fragment.initialize_js('HTMLAcademyXBlockStudentView')
        return fragment

    def studio_view(self, context):

        template_context = {
            'metadata': json.dumps({
                'display_name': self.display_name,
                'course_name': self.course_name,
                'iteration_id': self.iteration_id,
                'course_element': self.course_element,
                'content': self.description,
                'points': self.weight,
                'lab_url': self.lab_url,
                'api_url': self.api_url,
                'secret_key': self.secret_key
            }),
        }

        if context is None:
            context = dict()

        context.update(template_context)

        fragment = Fragment()
        fragment.add_content(self.load_template('studio_view.html', context))
        fragment.add_css(self.load_css('studio_view.css'))
        fragment.add_javascript(self.load_js('studio_view.js'))
        fragment.initialize_js('HTMLAcademyXBlockStudioView')
        return fragment

    def get_score(self):
        return {
            'score': self._get_points() * self.weight,
            'total': self.weight,
        }

    def max_score(self):
        return self.weight

    #==================================================================================================================#

    @XBlock.json_handler
    def save_settings(self, data, suffix):
        self.display_name = data.get('display_name')
        self.course_name = data.get('course_name')
        self.iteration_id = data.get('iteration_id')
        self.course_element = data.get('course_element')
        self.description = data.get('content')
        self.weight = data.get('points')
        self.lab_url = data.get('lab_url')
        self.api_url = data.get('api_url')
        self.secret_key = data.get('secret_key')
        return '{}'

    @XBlock.handler
    def start_lab(self, request, suffix=''):

        html_academy_link = self.lab_url.format(
            name=self.course_name,
            element=self.course_element,
        )

        return HTTPFound(location=html_academy_link)

    @XBlock.json_handler
    def staff_info(self, data, suffix=''):
        assert self._is_staff()
        outputs = ""
        if data != {}:
            if 'user' in data:
                user = data['user']
                r = UsageKey.from_string(self.location.__unicode__())
                s = None
                try:
                    s = StudentModule.objects.get(student__username=user,
                          module_state_key=r)
                    outputs = s.state

                except Exception:
                    outputs = "User %s didn't participate" % user

        return {'data': outputs}

    @XBlock.handler
    def check_by_academy(self, request, suffix=''):
        email = ""
        hashs = ""

        try:
            email = request.GET['email']
            hashs = request.GET['hash']
        except Exception:
            return Response("email and hash parameters required")

        hash_to_be = self._md5("%s:%s" % (email, self.secret_key))
        if hash_to_be != hashs:
            return Response("Wrong hash")

        r = UsageKey.from_string(self.location.__unicode__())
        s = None
        try:
            s = StudentModule.objects.get(student__email=email,
                          module_state_key=r)
        except Exception:
            return Response("User not found")

        state = json.loads(s.state)
        history = state['history']

        ext_response = self._do_external_request(email, self.iteration_id)

        points_earned = 0
        # Find course we are checking
        for element in ext_response:
            # FIXME Pretty brave assumption, make it error-prone
            if int(self.course_element) == element['course_number']:
                # Ew, gross!
                points_earned = round(float(element['tasks_completed']) / element['tasks_total'], 2)
                history = json.dumps(self._update_state(history, element['tasks_progress'], points_earned))
                break

        state['history'] = history
        s.state = json.dumps(state)
        s.save()

        return Response("OK")

    def _update_state(self, state, tasks_progress, new_score):
        """
        state - current state from StudentModule
        tasks_progress - raw data from HTML Academy
        new_score - new rating from HTML Academy
        """
        states = json.loads(state)
        max_date_in_progress = datetime.datetime.strptime(max(tasks_progress, key=lambda x: datetime.datetime.strptime(x['date'], '%Y-%m-%d %H:%M:%S'))['date'], '%Y-%m-%d %H:%M:%S')

        if len(states) > 0:  # There are elements in history
            max_date_in_hist = datetime.datetime.strptime(max(states, key=lambda x: datetime.datetime.strptime(x.keys()[0], '%Y-%m-%d %H:%M:%S')).keys()[0], '%Y-%m-%d %H:%M:%S')
            if max_date_in_progress > max_date_in_hist:  # From HTML Academy is new rating
                if self._allow_checking(max_date_in_progress):
                    states.append({max_date_in_progress.strftime('%Y-%m-%d %H:%M:%S'): new_score})

        else:  # There are no elements in history
            if len(tasks_progress) > 0:  # There are some history from HTML Academy
                if self._allow_checking(max_date_in_progress):
                    states.append({max_date_in_progress.strftime('%Y-%m-%d %H:%M:%S'): new_score})

        return states

    @XBlock.json_handler  # Manual pressing
    def check_lab(self, data, suffix):
        user_email = self.runtime.get_real_user(self.runtime.anonymous_student_id).email
        ext_response = self._do_external_request(user_email, self.iteration_id)

        points_earned = 0

        # Find course we are checking
        for element in ext_response:
            # FIXME Pretty brave assumption, make it error-prone
            if int(self.course_element) == element['course_number']:
                # Ew, gross!
                points_earned = round(float(element['tasks_completed']) / element['tasks_total'], 2)
                self.history = json.dumps(self._update_state(self.history, element['tasks_progress'], points_earned))

                break

        # msg = "Your total score: %s" % (points_earned,)
        # status = 'incorrect' if points_earned == 0 else 'correct' if points_earned == 1 else 'partially'

        return json.dumps(self._get_student_context())

    def _get_points(self):
        array = json.loads(self.history)
        if len(array) > 0:
            history = array[-1]
            return history[history.keys()[0]]
        else:
            return 0

    def _get_attempts(self):
        history = json.loads(self.history)
        return len(history)

    #==================================================================================================================#

    def _get_student_context(self, user=None):
        context = {
            'id': self.location.name.replace('.', '_'),
            'student_state': json.dumps(
                {
                    'meta': {
                        'name': self.display_name,
                        'text': self.description,
                    },
                    'score': {
                        'earned': self._get_points() * self.weight,
                        'max': self.weight,
                        'string': self._get_score_string(),
                    },
                }
            ),
            'is_staff': getattr(self.xmodule_runtime, 'user_is_staff', False),

            # This is probably studio, find out some more ways to determine this
            'is_studio': self.scope_ids.user_id is None,
            'allow_checking': self._allow_checking_now()
        }

        if self._is_staff():
            context['check_by_academy_url'] = self.runtime.handler_url(self, 'check_by_academy', thirdparty=True)
            context['state'] = json.dumps({
                'course_name': self.course_name,
                'iteration_id': self.iteration_id,
                'course_element': self.course_element,
                'weight': self.weight,
                'lab_url': self.lab_url,
                'api_url': self.api_url
            }, indent=2)

        return context

    def _get_score_string(self):
        result = ''
        if self.weight is not None and self.weight != 0:
            if self._get_attempts() > 0:
                result = '(%s/%s points)' % (self._get_points() * self.weight, self.weight,)
            else:
                result = '(%s points possible)' % (self.weight,)
        return result

    def _do_external_request(self, user_email, iteration_id):
        h = self._md5('%s:%s:%s' % (iteration_id, user_email, self.secret_key))
        url = self.api_url.format(email=user_email, iterationID=iteration_id, hash=h)
        try:
            request = requests.post(url)
        except Exception:
            raise Exception('Cannot connect to HTMLAcademy')
        if (not request.text) or (not request.text.strip()):
            raise Exception('Empty answer from HTMLAcademy')
        try:
            response_json = json.loads(request.text)
        except Exception:
            raise Exception('Cannot parse response from HTMLAcademy')
        return response_json

    @staticmethod
    def _md5(inputs):
        m = hashlib.md5()
        m.update(inputs)
        return m.hexdigest()

    def _is_staff(self):
        return getattr(self.xmodule_runtime, 'user_is_staff', False)

    def _allow_checking_now(self):
        due = get_extended_due_date(self)
        if due is not None:
            return self._now() < due
        return True

    def _allow_checking(self, dt):
        dt = dt.replace(tzinfo=pytz.utc)  # Let it be...
        due = get_extended_due_date(self)
        if due is not None:
            return dt < due
        return True

    def _now(self):
        """
        Get current date and time.
        """
        return datetime.datetime.utcnow().replace(tzinfo=pytz.utc)