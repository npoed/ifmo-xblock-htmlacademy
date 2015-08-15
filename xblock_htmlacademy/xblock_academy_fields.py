from xblock.fields import Scope, Integer, String, Float


class HTMLAcademyXBlockFields(object):

    display_name = String(
        display_name="Display name",
        default='HTMLAcademy Assignment',
        help="This name appears in the horizontal navigation at the top of the page.",
        scope=Scope.settings
    )

    course_name = String(
        display_name="Course name",
        scope=Scope.settings
    )

    iteration_id = String(
        display_name="Course short name",
        scope=Scope.settings
    )

    course_element = String(
        display_name="Course element",
        scope=Scope.settings
    )

    description = String(
        display_name="Description",
        scope=Scope.settings
    )

    weight = Float(
        display_name="Max score",
        scope=Scope.settings,
        default=0,
    )

    lab_url = String(
        display_name="URL to open lab",
        scope=Scope.settings,
        default="https://npoed.htmlacademy.ru/{name}/course/{element}"
    )

    api_url = String(
        display_name="URL to get into API",
        scope=Scope.settings,
        default="https://npoed.htmlacademy.ru/api/getprogress?user_id={email}&module_id={iterationID}&hash={hash}"
    )

    secret_key = String(
        display_name="Key for hashing API request",
        scope=Scope.settings,
        default="f*n,2Ch"
    )

    points = Float(
        scope=Scope.user_state,
        default=0,
    )

    attempts = Integer(
        scope=Scope.user_state,
        default=0,
    )

    """
    [{"10.05.2015 10:00:00" : 0.07}, {"10.05.2015 10:05:00" : 0.14}]
    """
    history = String(
        scope=Scope.user_state,
        default="[]"
    )