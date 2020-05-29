import os

from version import VERSION


class Config:
    VERSION = VERSION

    SECRET_KEY = os.environ.get('SECRET_KEY', '')

    REQUEST_DATA = {
        "format": "json",
        "backend": "es",
    }

    CONFIDENCE_MAPPING = {

    }

    USER_AGENT = ('Cisco Threat Response Integrations '
                  '<tr-integrations-support@cisco.com>')

    API_URL = 'https://www.c1fapp.com/cifapp/api/'

