from http import HTTPStatus

from pytest import fixture
from unittest.mock import patch

from .utils import headers


def routes():
    yield '/deliberate/observables'
    yield '/observe/observables'
    yield '/refer/observables'


@fixture(scope='module', params=routes(), ids=lambda route: f'POST {route}')
def route(request):
    return request.param


def test_enrich_call_with_invalid_jwt_failure(
    route, client, invalid_jwt, invalid_jwt_expected_payload
):
    response = client.post(route, headers=headers(invalid_jwt))

    assert response.status_code == HTTPStatus.OK
    assert response.json == invalid_jwt_expected_payload


@fixture(scope='module')
def invalid_json():
    return [{'type': 'domain'}]


def test_enrich_call_with_valid_jwt_but_invalid_json_failure(
    route, client, valid_jwt, invalid_json, invalid_json_expected_payload,
):
    response = client.post(
        route, headers=headers(valid_jwt), json=invalid_json
    )

    assert response.status_code == HTTPStatus.OK
    assert response.json == invalid_json_expected_payload


@fixture(scope='module')
def valid_json():
    return [{'type': 'domain', 'value': 'onedrive.live.com'}]


@patch('requests.post')
def test_enrich_call_success(
        mock_request, route, client, valid_jwt, valid_json, c1fapp_response_ok
):

    mock_request.return_value = c1fapp_response_ok

    response = client.post(
        route, headers=headers(valid_jwt), json=valid_json
    )

    assert response.status_code == HTTPStatus.OK

    data = response.get_json()
    if route == '/observe/observables':
        assert data["data"]["sightings"]["docs"][0]["confidence"]
        assert data["data"]["sightings"]["docs"][0]["id"]
        assert data["data"]["sightings"]["docs"][0]["count"]
        assert data["data"]["sightings"]["docs"][0]["observed_time"]
        assert data["data"]["sightings"]["docs"][0]["schema_version"]
        assert data["data"]["sightings"]["docs"][0]["type"]
