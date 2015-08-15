from django.contrib.auth.models import User
from webob.exc import HTTPFound
from xblock.core import XBlock
from xblock.fragment import Fragment
from xblock_academy_fields import HTMLAcademyXBlockFields
from xblock_academy_resources import XBlockResources

import json
import requests


class HTMLAcademyXBlock(HTMLAcademyXBlockFields, XBlockResources, XBlock):

    icon_class = 'problem'
    has_score = True
    package = __package__

    # Use this unless submissions api is used
    always_recalculate_grades = True

    ACADEMY_API_URL = 'https://htmlacademy.ru/api/get_progress?course={short_name}&ifmo_user_id={user}'
    ACADEMY_LAB_URL = 'https://htmlacademy.ru/{name}/{element}'

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
                'course_short_name': self.course_short_name,
                'course_element': self.course_element,
                'content': self.description,
                'points': self.weight,
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
            'score': self.points * self.weight,
            'total': self.weight,
        }

    def max_score(self):
        return self.weight

    #==================================================================================================================#

    @XBlock.json_handler
    def save_settings(self, data, suffix):
        self.display_name = data.get('display_name')
        self.course_name = data.get('course_name')
        self.course_short_name = data.get('course_short_name')
        self.course_element = data.get('course_element')
        self.description = data.get('content')
        self.weight = data.get('points')
        return '{}'

    @XBlock.handler
    def start_lab(self, request, suffix=''):

        html_academy_link = self.ACADEMY_LAB_URL.format(
            name=self.course_name,
            element=self.course_element,
        )

        return HTTPFound(location=html_academy_link)

    @XBlock.json_handler
    def check_lab(self, data, suffix):
        self.attempts += 1

        username = User.objects.get(id=self.scope_ids.user_id).username
        ext_response = self._do_external_request(username, self.course_short_name)

        points_earned = 0

        # Find course we are checking
        for element in ext_response:
            # FIXME Pretty brave assumption, make it error-prone
            if int(self.course_element) == element['course_number']:
                # Ew, gross!
                points_earned = float(element['tasks_completed']) / element['tasks_total']
                break

        # msg = "Your total score: %s" % (points_earned,)
        # status = 'incorrect' if points_earned == 0 else 'correct' if points_earned == 1 else 'partially'

        self.points = points_earned

        return json.dumps(self._get_student_context())

    #==================================================================================================================#

    def _get_student_context(self, user=None):
        return {
            'student_state': json.dumps(
                {
                    'meta': {
                        'name': self.display_name,
                        'text': self.description,
                    },
                    'score': {
                        'earned': self.points * self.weight,
                        'max': self.weight,
                        'string': self._get_score_string(),
                    },
                }
            ),
            'is_staff': getattr(self.xmodule_runtime, 'user_is_staff', False),

            # This is probably studio, find out some more ways to determine this
            'is_studio': self.scope_ids.user_id is None
        }

    def _get_score_string(self):
        result = ''
        if self.weight is not None and self.weight != 0:
            if self.attempts > 0:
                result = '(%s/%s points)' % (self.points * self.weight, self.weight,)
            else:
                result = '(%s points possible)' % (self.weight,)
        return result

    def _do_external_request(self, sso_id=0, short_name=''):
        url = self.ACADEMY_API_URL.format(user=sso_id, short_name=short_name)
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
