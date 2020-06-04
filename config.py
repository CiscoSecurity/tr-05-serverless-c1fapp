import os

from version import VERSION


class Config:
    VERSION = VERSION

    SECRET_KEY = os.environ.get('SECRET_KEY', '')

    REQUEST_DATA = {
        "format": "json",
        "backend": "es",
    }

    USER_AGENT = ('Cisco Threat Response Integrations '
                  '<tr-integrations-support@cisco.com>')

    API_URL = 'https://www.c1fapp.com/cifapp/api/'

    CONFIDENCE_MAPPING = {
     range(26): 'Low',
     range(26, 80): 'Medium',
     range(80, 101): 'High'
    }

    CTR_ENTITIES_LIMIT_DEFAULT = 100
    CTR_ENTITIES_LIMIT_MAX = 1000

    try:
        CTR_ENTITIES_LIMIT = int(os.environ['CTR_ENTITIES_LIMIT'])
        assert CTR_ENTITIES_LIMIT > 0
    except (KeyError, ValueError, AssertionError):
        CTR_ENTITIES_LIMIT = CTR_ENTITIES_LIMIT_DEFAULT

    if CTR_ENTITIES_LIMIT > CTR_ENTITIES_LIMIT_MAX:
        CTR_ENTITIES_LIMIT = CTR_ENTITIES_LIMIT_MAX
