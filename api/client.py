import json
import requests

from flask import current_app

from api.errors import UnexpectedC1fAppError


class C1fAppClient:
    def __init__(self, api_key):
        self.api_url = current_app.config['API_URL']
        self.headers = {
            'User-Agent': current_app.config['USER_AGENT']
        }
        self.data = {
            **current_app.config['REQUEST_DATA'],
            'key': api_key
        }

    def get_c1fapp_response(self, observable):
        self.data.update({'request': observable})

        response = requests.post(
            self.api_url, headers=self.headers, data=json.dumps(self.data)
        )

        if not response.ok:
            raise UnexpectedC1fAppError(response)

        return response.json
