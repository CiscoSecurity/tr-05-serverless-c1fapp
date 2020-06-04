from functools import partial

from flask import Blueprint, g, current_app
from api.client import C1fAppClient
from api.mappings import Mapping

from api.schemas import ObservableSchema
from api.utils import get_json, get_jwt, jsonify_data, jsonify_result

enrich_api = Blueprint('enrich', __name__)


get_observables = partial(get_json, schema=ObservableSchema(many=True))


@enrich_api.route('/deliberate/observables', methods=['POST'])
def deliberate_observables():
    # Not implemented
    return jsonify_data({})


@enrich_api.route('/observe/observables', methods=['POST'])
def observe_observables():
    key = get_jwt().get('key', '')

    client = C1fAppClient(key)
    observables = get_observables()

    g.sightings = []

    limit = current_app.config['CTR_ENTITIES_LIMIT']

    for observable in observables:
        mapping = Mapping.for_(observable)

        if mapping:
            response_data = client.get_c1fapp_response(observable['value'])
            g.sightings.extend(
                mapping.extract_sightings(response_data, limit)
            )

    return jsonify_result()


@enrich_api.route('/refer/observables', methods=['POST'])
def refer_observables():
    # Not implemented
    return jsonify_data([])
