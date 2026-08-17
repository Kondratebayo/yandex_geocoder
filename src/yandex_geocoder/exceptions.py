class YandexGeocoderException(Exception):
    """Base exception for the Yandex Geocoder SDK."""


class AuthenticationError(YandexGeocoderException):
    """Base exception for authentication errors."""


class TokenNotFoundError(AuthenticationError):
    """Raised when the API token is not provided."""


class InvalidParamsError(YandexGeocoderException):
    """Raised when request parameters are invalid."""


class UnexpectedResponseError(YandexGeocoderException):
    """Raised when the API response is unexpected or invalid."""


class RequestError(YandexGeocoderException):
    """Base exception for HTTP request errors."""


class RequestTimeoutError(RequestError):
    """Raised when an HTTP request times out."""


class BadRequestError(RequestError):
    """Raised when the API returns HTTP 400 Bad Request."""


class UnauthorizedError(RequestError):
    """Raised when the API returns HTTP 401 Unauthorized."""


class ForbiddenError(RequestError):
    """Raised when the API returns HTTP 403 Forbidden."""


class RateLimitError(RequestError):
    """Raised when the API returns HTTP 429 Too Many Requests."""


class ServerError(RequestError):
    """Raised when the API returns an HTTP 5xx server error."""