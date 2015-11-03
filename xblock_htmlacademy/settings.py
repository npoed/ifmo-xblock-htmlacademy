SELECTED_CONFIGURATION = 'ifmo'

CONFIGURATIONS = {
    'npoed': {
        'LAB_URL': 'https://npoed.htmlacademy.ru/{name}/course/{element}',
        'API_URL': 'https://npoed.htmlacademy.ru/api/getprogress?username={login}&module_id={iterationID}&hash={hash}',
        'SECRET': 'f*n,2Ch',
    },
    'ifmo': {
        'LAB_URL': 'https://npoed.htmlacademy.ru/{name}/course/{element}',
        'API_URL': 'https://npoed.htmlacademy.ru/api/getprogress?username={login}&module_id={iterationID}&hash={hash}',
        'SECRET': 'f*n,2Ch',
    },
    'default': {
        'LAB_URL': None,
        'API_URL': None,
        'SECRET': None,
    }
}

CONFIGURATION = CONFIGURATIONS.get(SELECTED_CONFIGURATION)
