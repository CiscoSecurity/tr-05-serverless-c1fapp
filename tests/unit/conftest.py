from datetime import datetime
from http import HTTPStatus
from unittest.mock import MagicMock

from authlib.jose import jwt
from pytest import fixture

from api.errors import PERMISSION_DENIED, INVALID_ARGUMENT, FORBIDDEN
from app import app


@fixture(scope='session')
def secret_key():
    # Generate some string based on the current datetime.
    return datetime.utcnow().isoformat()


@fixture(scope='session')
def client(secret_key):
    app.secret_key = secret_key

    app.testing = True

    with app.test_client() as client:
        yield client


def c1fapp_api_response_mock(status_code, payload=None):
    mock_response = MagicMock()

    mock_response.status = status_code
    mock_response.ok = status_code == HTTPStatus.OK

    payload = payload or []

    mock_response.json = lambda: payload

    return mock_response


def c1fapp_api_error_mock(status_code, text=None):
    mock_response = MagicMock()

    mock_response.status_code = status_code
    mock_response.ok = status_code == HTTPStatus.OK

    mock_response.text = text

    return mock_response


@fixture(scope='function')
def c1fapp_response_ok():
    return c1fapp_api_response_mock(
        HTTPStatus.OK, payload=[
            {
                "feed_label": [
                    "Phishtank"
                ],
                "domain": [
                    "onedrive.live.com"
                ],
                "description": [
                    "Microsoft"
                ],
                "derived": "direct",
                "address": [
                    "https://onedrive.live.com/?authkey=%21AG7v3K%5Fv%5Fvmx0wU"
                ],
                "ip_address": [
                    "13.107.42.13"
                ],
                "asn": [
                    "-"
                ],
                "confidence": [
                    95
                ],
                "country": [
                    "US"
                ],
                "reportime": [
                    "2020-04-12"
                ],
                "source": [
                    "http://www.phishtank.com/phish_detail.php?phish_id=62",
                    "http://www.phishtank.com/phish_detail.php?phish_id=62"
                ],
                "asn_desc": [
                    "-"
                ],
                "assessment": [
                    "phishing"
                ]
            }
        ]
    )


@fixture(scope='session')
def c1fapp_response_unauthorized_creds(secret_key):
    return c1fapp_api_error_mock(
        HTTPStatus.FORBIDDEN,
        'Invalid API key'
    )


@fixture(scope='session')
def unauthorized_creds_body():
    return {
        'data': {},
        'errors': [
            {'code': FORBIDDEN,
             'message': 'Unexpected response from C1fApp: Invalid API key',
             'type': 'fatal'
             }
        ]
    }


@fixture(scope='session')
def valid_jwt(client):
    header = {'alg': 'HS256'}

    payload = {'username': 'gdavoian', 'superuser': False}

    secret_key = client.application.secret_key

    return jwt.encode(header, payload, secret_key).decode('ascii')


@fixture(scope='session')
def invalid_jwt(valid_jwt):
    header, payload, signature = valid_jwt.split('.')

    def jwt_decode(s: str) -> dict:
        from authlib.common.encoding import urlsafe_b64decode, json_loads
        return json_loads(urlsafe_b64decode(s.encode('ascii')))

    def jwt_encode(d: dict) -> str:
        from authlib.common.encoding import json_dumps, urlsafe_b64encode
        return urlsafe_b64encode(json_dumps(d).encode('ascii')).decode('ascii')

    payload = jwt_decode(payload)

    # Corrupt the valid JWT by tampering with its payload.
    payload['superuser'] = True

    payload = jwt_encode(payload)

    return '.'.join([header, payload, signature])


@fixture(scope='module')
def invalid_jwt_expected_payload(route):
    if route in ('/observe/observables', '/health'):
        return {
            'data': {},
            'errors': [
                {'code': PERMISSION_DENIED,
                 'message': 'Invalid Authorization Bearer JWT.',
                 'type': 'fatal'}
            ]
        }

    if route.endswith('/deliberate/observables'):
        return {'data': {}}

    if route.endswith('/refer/observables'):
        return {'data': []}


@fixture(scope='module')
def invalid_json_expected_payload(route, client):
    if route.endswith('/observe/observables'):
        return {
            'data': {},
            'errors':
                [
                {'code': INVALID_ARGUMENT,
                 'message':
                     "Invalid JSON payload received. "
                     "{0: {'value': ['Missing data for required field.']}}",
                 'type': 'fatal'}
            ]
        }

    if route.endswith('/deliberate/observables'):
        return {'data': {}}

    return {'data': []}


def expected_payload(r, body):
    if r.endswith('/deliberate/observables'):
        return {'data': {}}

    if r.endswith('/refer/observables'):
        return {'data': []}

    return body


@fixture(scope='module')
def success_enrich_body():
    return {
        'data':
            {
                'sightings':
                    {'count': 1,
                     'docs': [
                         {'confidence': 'High',
                          'count': 1,
                          'description': 'Seen on C1fApp feed',
                          'observables': [
                              {'type': 'domain',
                               'value': 'onedrive.live.com'}
                          ],
                          'observed_time': {'start_time': '2020-04-12T00:00:00Z'},
                          'relations': [
                              {'origin': 'С1fApp Enrichment Module',
                               'related': {'type': 'ip',
                                           'value': '13.107.42.13'},
                               'relation': 'Resolved_to',
                               'source': {'type': 'domain',
                                          'value': 'onedrive.live.com'}
                               }
                          ],
                          'schema_version': '1.0.17',
                          'source': 'C1fApp',
                          'source_uri':
                              'http://www.phishtank.com/phish_detail.php?phish_id=62',
                          'type': 'sighting'
                          }
                     ]
                     },
                "indicators": {
                    "count": 1,
                    "docs": [
                        {
                            "confidence": "High",
                            "schema_version": "1.0.17",
                            "short_description": "Phishtank",
                            "tags": [
                                "phishing"
                            ],
                            "tlp": "white",
                            "type": "indicator",
                            "producer": "C1fApp",
                            "valid_time": {},
                        }
                    ]
                }
            }
    }


@fixture(scope='module')
def success_enrich_expected_payload(route, success_enrich_body):
    return expected_payload(route, success_enrich_body)
