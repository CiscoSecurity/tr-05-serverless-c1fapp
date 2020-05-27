from flask import Blueprint
from api.client import C1fAppClient
from api.utils import get_jwt, jsonify_data

health_api = Blueprint('health', __name__)


@health_api.route('/health', methods=['POST'])
def health():
    key = get_jwt().get('key', '')

    client = C1fAppClient(key)
    _ = client.lookup('test.com')

    return jsonify_data({'status': 'ok'})
