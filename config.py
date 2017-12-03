import os


SETTINGS = {
    'own_space': {
        'login': os.environ.get('OWN_SPACE_LOGIN', ''),
        'password': os.environ.get('OWN_SPACE_PASSWORD', ''),
    }
}
