class YandexGeocoderException(Exception):
    """Base exception for Yandex Geocoder SDK."""


class AuthenticationError(YandexGeocoderException):
    """Authentication related error."""


class TokenNotFoundError(AuthenticationError):
    """API token was not provided."""


class InvalidParamsError(Exception):
    """Raised when request parameters are invalid."""


class UnexpectedResponseError(Exception):
    """Raised when request parameters are invalid."""


class RequestError(YandexGeocoderException):
    """HTTP request failed."""


class BadRequestError(RequestError):
    """HTTP 400."""


class UnauthorizedError(RequestError):
    """HTTP 401."""


class ForbiddenError(RequestError):
    """HTTP 403."""


class RateLimitError(RequestError):
    """HTTP 429."""


class ServerError(RequestError):
    """HTTP 5xx."""
