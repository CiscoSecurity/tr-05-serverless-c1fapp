from abc import ABCMeta, abstractmethod
from uuid import uuid4
from flask import current_app
from collections import defaultdict

from api.utils import all_subclasses, key_error_handler

CTIM_DEFAULTS = {
    'schema_version': '1.0.17',
}


class Mapping(metaclass=ABCMeta):

    def __init__(self, observable):
        self.observable = observable
        self.unique_feeds = defaultdict(lambda: defaultdict(list))

    @classmethod
    def for_(cls, observable):
        """Returns an instance of `Mapping` for the specified type."""

        for subcls in all_subclasses(Mapping):
            if subcls.type() == observable['type']:
                return subcls(observable)

        return None

    @classmethod
    @abstractmethod
    def type(cls):
        """Returns the observable type that the mapping is able to process."""

    @abstractmethod
    def _get_related(self, record):
        """Returns relation depending on an observable and related types."""

    @staticmethod
    def _map_confidence(confidence):
        confidence = int(confidence)
        for range_ in current_app.config['CONFIDENCE_MAPPING']:
            if confidence in range_:
                return current_app.config['CONFIDENCE_MAPPING'][range_]

    def _sighting(self, record):
        def observed_time():
            start_time = f"{record['reportime'][0]}T00:00:00Z"
            return {
                'start_time': start_time,
                'end_time': start_time
            }

        return {
            **CTIM_DEFAULTS,
            'id': f'transient:sighting-{uuid4()}',
            'type': 'sighting',
            'source': 'C1fApp',
            'source_uri': max(record['source'][0].split(','), key=len),
            'confidence': self._map_confidence(record['confidence'][0]),
            'count': 1,
            'description': 'Seen on C1fApp feed',
            'observables': [self.observable],
            'observed_time': observed_time(),
            'relations': self._get_related(record)
        }

    def _indicator(self, record):
        return {
            **CTIM_DEFAULTS,
            'id': f'transient:indicator-{uuid4()}',
            'type': 'indicator',
            'confidence': self._map_confidence(record['confidence'][0]),
            'tlp': 'white',
            'tags': record['assessment'],
            'short_description': record['feed_label'][0],
            'valid_time': {},
            'producer': 'C1fApp',
            'title': f'Feed: {record["feed_label"][0]}',
        }

    @staticmethod
    def _relationship(sighting_id, indicator_id):
        return {
            'id': f'transient:{uuid4()}',
            'source_ref': sighting_id,
            'target_ref': indicator_id,
            'relationship_type': 'member-of',
            'type': 'relationship',
            **CTIM_DEFAULTS
        }

    @key_error_handler
    def extract_sightings(self, response_data):
        result = []
        for record in response_data:
            feed_label = record['feed_label'][0]
            sighting = self._sighting(record)
            self.unique_feeds[feed_label]['sighting_ids'].append(
                sighting['id']
            )
            result.append(sighting)
        return result

    @key_error_handler
    def extract_indicators(self, response_data):
        result = []
        for record in response_data:
            feed_label = record['feed_label'][0]
            if not self.unique_feeds[feed_label].get('indicator_id'):
                indicator = self._indicator(record)
                result.append(indicator)
                self.unique_feeds[feed_label]['indicator_id'] = indicator['id']
        return result

    def extract_relationships(self):
        result = []
        unique_feeds = self.unique_feeds.keys()
        for feed in unique_feeds:
            for sighting_id in self.unique_feeds[feed]['sighting_ids']:
                indicator_id = self.unique_feeds[feed]['indicator_id']
                relationship = self._relationship(sighting_id, indicator_id)
                result.append(relationship)
        return result

    @staticmethod
    def observable_relation(relation_type, source, related):
        return {
            "origin": "С1fApp Enrichment Module",
            "relation": relation_type,
            "source": source,
            "related": related
        }


class Domain(Mapping):
    @classmethod
    def type(cls):
        return 'domain'

    def _get_related(self, record):
        result = []
        ips = record['ip_address']
        address = record['address']
        if 'http' in address[0] and record['domain'][0] \
                == self.observable['value']:
            result.append(self.observable_relation(
                'Contains',
                {'type': 'url', 'value': address[0]},
                {'type': 'domain', 'value': record['domain'][0]})
            )
        for ip in ips:
            if ip:
                result.append(self.observable_relation(
                    'Resolved_to',
                    self.observable,
                    {'type': 'ip', 'value': ip}
                )
                )
        return result


class IP(Mapping):
    @classmethod
    def type(cls):
        return 'ip'

    def _get_related(self, record):
        result = []
        domains = record['domain']
        for domain in domains:
            if domain not in ('', self.observable['value']):
                result.append(self.observable_relation(
                    'Resolved_to',
                    {'type': 'domain', 'value': domain},
                    self.observable)
                )
        return result


class URL(Mapping):
    @classmethod
    def type(cls):
        return 'url'

    def _get_related(self, record):
        result = []
        ips = record['ip_address']
        domains = record['domain']
        address = record['address']
        if 'http' in address[0]:
            for ip in ips:
                result.append(self.observable_relation(
                    'Hosted_By', self.observable, {'type': 'ip', 'value': ip}))
            for domain in domains:
                if domain in self.observable['value']:
                    result.append(self.observable_relation(
                        'Contains',
                        self.observable,
                        {'type': 'domain', 'value': domain})
                    )
        return result
