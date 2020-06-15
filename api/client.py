import requests

from flask import current_app

from api.errors import UnexpectedC1fAppError

NOT_CRITICAL_ERRORS = (
    'Unsupported request ? IPv4/Domain only',  # ToDo
    'Empty Search! Availiable search: IPv4/URL/Domain'
)


class C1fAppClient:
    def __init__(self, api_key):
        self.api_url = current_app.config['API_URL']
        self.headers = {
            'User-Agent': current_app.config['USER_AGENT'],
            'Content-Type': 'application/json'
        }
        self.data = {
            **current_app.config['REQUEST_DATA'],
            'key': api_key
        }

    def get_c1fapp_response(self, observable):
        self.data.update({'request': observable})

        response = requests.post(
            self.api_url, headers=self.headers, json=self.data
        )

        if response.text in NOT_CRITICAL_ERRORS:
            return []

        if response.ok:
            return response.json()

        raise UnexpectedC1fAppError(response)
