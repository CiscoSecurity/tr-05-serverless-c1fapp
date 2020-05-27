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
        current_app.config['REQUEST_DATA']['key'] = api_key
        self.data = current_app.config['REQUEST_DATA']

    def lookup(self, observable):
        data = {
            **self.data,
            'request': observable
        }

        response = requests.post(
            self.api_url, headers=self.headers, data=json.dumps(data)
        )

        if not response.ok:
            print(response)
            raise UnexpectedC1fAppError(response)

        return response.json
