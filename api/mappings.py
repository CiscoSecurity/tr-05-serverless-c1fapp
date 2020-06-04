from abc import ABCMeta, abstractmethod
from uuid import uuid4
from flask import current_app

from api.utils import all_subclasses

CTIM_DEFAULTS = {
    'schema_version': '1.0.17',
}


class Mapping(metaclass=ABCMeta):

    def __init__(self, observable):
        self.observable = observable

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
            start = record.get('reportime')
            return {'start_time': f'{start[0]}T00:00:00Z'}

        return {
            **CTIM_DEFAULTS,
            'id': f'transient:{uuid4()}',
            'type': 'sighting',
            'source': 'C1fApp',
            'source_uri': record.get('source')[0],
            'confidence': self._map_confidence(record.get('confidence')[0]),
            'count': 1,
            'description': 'Seen on C1fApp feed',
            'observables': [self.observable],
            'observed_time': observed_time(),
            'relations': self._get_related(record)
        }

    def extract_sightings(self, response_data, limit):
        response_data = response_data[:limit]
        result = []
        for record in response_data:
            sighting = self._sighting(record)
            result.append(sighting)
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
        ips = record.get('ip_address')
        for ip in ips:
            result.append(self.observable_relation(
                'Resolved_to', self.observable, {'type': 'ip', 'value': ip}))
        return result


class IP(Mapping):
    @classmethod
    def type(cls):
        return 'ip'

    def _get_related(self, record):
        result = []
        domains = record.get('domain')
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
        ips = record.get('ip_address')
        domains = record.get('domain')
        address = record.get('address')
        if 'http' in address[0]:
            for ip in ips:
                result.append(self.observable_relation(
                    'Hosted_By', self.observable, {'type': 'ip', 'value': ip}))
            for domain in domains:
                result.append(self.observable_relation(
                    'Contains',
                    self.observable,
                    {'type': 'domain', 'value': domain}
                )
                )
        return result
