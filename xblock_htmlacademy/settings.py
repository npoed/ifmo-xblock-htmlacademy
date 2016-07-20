from django.conf import settings

XBLOCK_SETTINGS = settings.XBLOCK_SETTINGS.get('IFMO_XBLOCK_HTMLACADEMY', {})
SELECTED_CONFIGURATION = XBLOCK_SETTINGS.get('SELECTED_CONFIGURATION', 'default')

SAMPLE_CONFIGURATIONS = {
    'npoed': {
        'LAB_URL': 'https://npoed.htmlacademy.ru/{name}/course/{element}',
        'API_URL': 'https://npoed.htmlacademy.ru/api/getprogress?username={login}&module_id={iterationID}&hash={hash}',
    },
    'ifmo': {
        'LAB_URL': 'https://npoed.htmlacademy.ru/{name}/course/{element}',
        'API_URL': 'https://npoed.htmlacademy.ru/api/getprogress?username={login}&module_id={iterationID}&hash={hash}',
    },
    'default': {
        'LAB_URL': None,
        'API_URL': None,
        'SECRET': None,
    }
}

SAMPLE_CONFIGURATION = SAMPLE_CONFIGURATIONS.get(SELECTED_CONFIGURATION, {})
CONFIGURATION = {
    'LAB_URL': XBLOCK_SETTINGS.get('LAB_URL', SAMPLE_CONFIGURATION.get('LAB_URL')),
    'API_URL': XBLOCK_SETTINGS.get('API_URL', SAMPLE_CONFIGURATION.get('API_URL')),
    'SECRET': XBLOCK_SETTINGS.get('SECRET', SAMPLE_CONFIGURATION.get('SECRET')),
}


def DefaultedDescriptor(base_class, default_condition=lambda x: x is None, **args):  # pylint: disable=invalid-name
    def __get__(self, xblock, xblock_class):
        value = super(self.__class__, self).__get__(xblock, xblock_class)
        return self._default if default_condition(value) else value
    derived_dict = {
        "__get__": __get__,
    }
    derived = type("%sNoneDefaulted" % base_class.__name__, (base_class,), derived_dict)
    return derived(**args)
