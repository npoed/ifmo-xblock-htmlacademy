# -*- coding: utf-8 -*-
import datetime

from webob.exc import HTTPFound, HTTPServerError
from webob import Response
from xblock.core import XBlock
from xblock.fragment import Fragment
from xblock_academy_fields import HTMLAcademyXBlockFields
from xblock_academy_resources import XBlockResources
from xmodule.util.duedate import get_extended_due_date
from opaque_keys.edx.keys import UsageKey
from webob.exc import HTTPOk
import hashlib
import json
import requests
import pytz


class HTMLAcademyXBlock(HTMLAcademyXBlockFields, XBlockResources, XBlock):

    icon_class = 'problem'
    has_score = True
    package = __package__
    always_recalculate_grades = True

    def student_view(self, context):

        if context is None:
            context = dict()

        context.update(self._get_student_context())

        fragment = Fragment()
        fragment.add_content(self.load_template('student_view.html', context))
        fragment.add_javascript(self.load_js('student_view.js'))
        fragment.add_css(self.load_css('lms_view.css'))
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
        self.lab_url = data.get('lab_url').strip() or None
        self.api_url = data.get('api_url').strip() or None
        self.secret_key = data.get('secret_key').strip() or None
        return '{}'

    @XBlock.handler
    def start_lab(self, request, suffix=''):
        self.started = True

        if self.course_name != '' and self.course_element != '' and self.iteration_id != '':

            html_academy_link = self.lab_url.format(
                name=self.course_name,
                element=self.course_element,
            )

            return HTTPFound(location=html_academy_link)
        else:
            return HTTPServerError(explanation='Course Name, Course Element and Iteration ID fields are required!')

    @XBlock.json_handler
    def staff_info(self, data, suffix=''):
        assert self._is_staff()
        from courseware.models import StudentModule
        outputs = "{}"
        if data != {}:
            if 'user_login' in data:
                user = data['user_login']
                r = UsageKey.from_string(self.location.__unicode__())
                s = None
                try:
                    s = StudentModule.objects.get(student__username=user,
                                                  module_state_key=r)
                    outputs = json.dumps(json.loads(s.state), indent=2)

                except Exception:
                    outputs = u'"Пользователь %s не просматривал задание"' % user

        return {'data': outputs}

    @XBlock.json_handler
    def reset_user_data(self, data, suffix=''):
        assert self._is_staff()
        from courseware.models import StudentModule
        user_login = data.get('user_login')
        try:
            module = StudentModule.objects.get(module_state_key=self.location,
                                               student__username=user_login)
            module.state = '{}'
            module.max_grade = None
            module.grade = None
            module.save()
            return {
                'state': "Состояние пользователя сброшено.",
            }
        except StudentModule.DoesNotExist:
            return {
                'state': "{Модуль для указанного пользователя не существует."
            }

    @XBlock.handler
    def check_by_academy(self, request, suffix=''):
        login = ""
        hashs = ""

        try:
            login = request.GET['login']
            hashs = request.GET['hash']
        except Exception:
            return Response("login and hash parameters required")

        hash_to_be = self._md5("%s:%s" % (login, self.secret_key))
        if hash_to_be != hashs:
            return Response("Wrong hash")

        r = UsageKey.from_string(self.location.__unicode__())
        s = None
        from courseware.models import StudentModule
        try:
            s = StudentModule.objects.get(student__username=login,
                          module_state_key=r)
        except Exception:
            return Response("User not found")

        state = json.loads(s.state)
        history = state.get('history', '[]')

        try:
            ext_response = self._do_external_request(login, self.iteration_id)
        except Exception as e:
            return Response(e.message)

        points_earned = 0
        # Find course we are checking
        for element in ext_response:
            if int(self.course_element) == element['course_number']:
                points_earned = round(float(element['tasks_completed']) / element['tasks_total'], 2)
                if points_earned > 0:
                    history = json.dumps(self._update_state(history, element['tasks_progress'], points_earned))
                break

        state['history'] = history
        s.state = json.dumps(state)
        s.save()

        return Response("OK")

    @XBlock.handler
    def get_grades_data(self, data, suffix=''):
        assert self._is_staff()
        from courseware.models import StudentModule
        grades_objects = StudentModule.objects.filter(module_state_key=self.location)
        grades = [['id', 'username', 'score', 'max_grade', 'state', 'created', 'modified']]
        for grade in grades_objects:
            try:
                history = json.loads(grade.state).get('history')
                has_history = True
            except Exception:
                history = None
                has_history = False
            grades.append([
                grade.id,
                grade.student.username if grade.student is not None else None,
                self._get_points(history)*self.weight if has_history else None,
                self.weight,
                grade.state,
                grade.created,
                grade.modified,
            ])
        return HTTPOk(
            body="\n".join(["\t".join(["" if j is None else str(j) for j in i]) for i in grades]),
            headers={
                'Content-Disposition': 'attachment; filename=grades_%s.tsv' % self.scope_ids.usage_id.block_id,
                'Content-Type': 'text/tab-separated-values'
            })

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

        if self.course_name == '' or self.course_element == '' or self.iteration_id == '':
            context = self._get_student_context()
            context['error'] = 'Course Name, Course Element and Iteration ID fields are required!'
            return json.dumps(context)

        if self.runtime.get_real_user is None:
            context = self._get_student_context()
            context['error'] = 'It seems to be requested in studio!'
            return json.dumps(context)

        staff_check = False
        if data.get('user_login') is not None:
            assert self._is_staff()
            staff_check = True
            user_login = data.get('user_login')
        else:
            user_login = self.runtime.get_real_user(self.runtime.anonymous_student_id).username

        from courseware.models import StudentModule
        student_module = None
        if staff_check:
            usage_key = UsageKey.from_string(self.location.__unicode__())
            try:
                student_module = StudentModule.objects.get(student__username=user_login,
                                                           module_state_key=usage_key)
            except StudentModule.DoesNotExist:
                return {
                    "error": "Пользовательский модуль не найден"
                }

        try:
            ext_response = self._do_external_request(user_login, self.iteration_id)
        except Exception as e:
            context = self._get_student_context()
            context['error'] = e.message
            return json.dumps(context)

        points_earned = 0

        # Find course we are checking
        for element in ext_response:
            if int(self.course_element) == element['course_number']:
                points_earned = round(float(element['tasks_completed']) / element['tasks_total'], 2)
                if points_earned > 0:
                    if not staff_check:
                        self.history = json.dumps(
                            self._update_state(self.history, element['tasks_progress'], points_earned)
                        )
                        self.runtime.publish(self, 'grade', {
                            'value': self.get_score()['score'],
                            'max_value': self.get_score()['total'],
                        })
                    else:
                        state = json.loads(student_module.state)
                        state['history'] = json.dumps(
                            self._update_state(state.get('history', '[]'), element['tasks_progress'], points_earned)
                        )
                        student_module.state = json.dumps(state)
                        student_module.save()

                break

        return json.dumps(self._get_student_context())

    def _get_points(self, history=None):
        array = json.loads(self.history if history is None else history)
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
            'allow_checking': self._allow_checking_now(),
            'error': '',

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
            context['get_grades_data'] = self.runtime.handler_url(self, 'get_grades_data', thirdparty=True).replace('_noauth', '')

        return context

    def _get_score_string(self):
        result = ''
        if self.weight is not None and self.weight != 0:
            if self._get_attempts() > 0:
                result = '(%s/%s баллов)' % (self._get_points() * self.weight, self.weight,)
            else:
                result = '(%s возможный балл)' % (self.weight,)
        return result

    def _do_external_request(self, user_login, iteration_id):
        h = self._md5('%s:%s:%s' % (iteration_id, user_login, self.secret_key))
        url = self.api_url.format(login=user_login, iterationID=iteration_id, hash=h)
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
        # HTML Academy возращает время по МСК без указания таймзоны, поэтому приведём руками
        tz = pytz.timezone('Europe/Moscow')
        dt = tz.localize(dt.replace(tzinfo=None))
        due = get_extended_due_date(self)
        if due is not None:
            return dt < due
        return True

    def _now(self):
        """
        Get current date and time.
        """
        return datetime.datetime.utcnow().replace(tzinfo=pytz.utc)
