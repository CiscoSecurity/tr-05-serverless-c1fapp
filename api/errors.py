from http import HTTPStatus

INVALID_ARGUMENT = 'invalid argument'
PERMISSION_DENIED = 'permission denied'
FORBIDDEN = 'forbidden'
UNKNOWN = 'unknown'
TOO_MANY_REQUESTS = 'too many requests'
UNAUTHORIZED = 'unauthorized'
NOT_FOUND = 'not found'
UNAVAILABLE = 'unavailable'
KEY_ERROR = 'key error'


class TRFormattedError(Exception):
    def __init__(self, code, message, type_='fatal'):
        super().__init__()
        self.code = code or UNKNOWN
        self.message = message or 'Something went wrong.'
        self.type_ = type_

    @property
    def json(self):
        return {'type': self.type_,
                'code': self.code,
                'message': self.message}


class InvalidJWTError(TRFormattedError):
    def __init__(self):
        super().__init__(
            PERMISSION_DENIED,
            'Invalid Authorization Bearer JWT.'
        )


class InvalidArgumentError(TRFormattedError):
    def __init__(self, error):
        super().__init__(
            INVALID_ARGUMENT,
            f'Invalid JSON payload received. {error}'
        )


class UnexpectedC1fAppError(TRFormattedError):
    def __init__(self, response):

        status_code_map = {
            HTTPStatus.BAD_REQUEST: INVALID_ARGUMENT,
            HTTPStatus.UNAUTHORIZED: UNAUTHORIZED,
            HTTPStatus.FORBIDDEN: FORBIDDEN,
            HTTPStatus.NOT_FOUND: NOT_FOUND,
            HTTPStatus.TOO_MANY_REQUESTS: TOO_MANY_REQUESTS,
            HTTPStatus.INTERNAL_SERVER_ERROR: UNKNOWN,
            HTTPStatus.SERVICE_UNAVAILABLE: UNKNOWN,
        }
        super().__init__(
            status_code_map.get(response.status_code),
            f'Unexpected response from C1fApp: {response.text}'
        )


class C1fAppKeyError(TRFormattedError):
    def __init__(self):

        super().__init__(
            code=KEY_ERROR,
            message='The data structure of C1fApp API has changed. '
                    'The module is broken.'
        )


class C1fAppSSLError(TRFormattedError):
    def __init__(self, exception):
        message = getattr(
            exception.args[0].reason.args[0], 'verify_message', ''
        ) or exception.args[0].reason.args[0].args[0]
        super().__init__(
            code=UNKNOWN,
            message=f'Unable to verify SSL certificate: {message}'
        )
