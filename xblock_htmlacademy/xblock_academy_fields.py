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

    course_short_name = String(
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

    points = Float(
        scope=Scope.user_state,
        default=0,
    )

    attempts = Integer(
        scope=Scope.user_state,
        default=0,
    )