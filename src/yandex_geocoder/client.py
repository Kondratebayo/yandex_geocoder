from __future__ import annotations

import logging
import os
import platform
from collections.abc import Mapping
from typing import Any, TypeVar, Unpack, overload

import httpx2
from pydantic import SecretStr, ValidationError

from yandex_geocoder._constants import (
    API_VERSION,
    YANDEX_API_KEY,
    YANDEX_BASE_URL,
)
from yandex_geocoder._errors import handle_query_exception
from yandex_geocoder.exceptions import (
    BadRequestError,
    ForbiddenError,
    InvalidParamsError,
    RateLimitError,
    RequestError,
    TokenNotFoundError,
    UnauthorizedError,
    UnexpectedResponseError,
)
from yandex_geocoder.models.params import (
    BaseGeocoderParams,
    ForwardGeocoderParams,
    ForwardKwargs,
    ReverseGeocoderParams,
    ReverseKwargs,
)
from yandex_geocoder.models.response import GeocodeErrorResponse, GeocodeResponse

# TODO: retry logic, error handling

logger = logging.getLogger(__name__)


P = TypeVar(
    "P",
    ForwardGeocoderParams,
    ReverseGeocoderParams,
)


class YandexGeocoderClient:
    _YANDEX_GEOCODER_URL = "https://geocode-maps.yandex.ru/1.x/"
    _YANDEX_GEOCODER_VERSION = API_VERSION

    def __init__(
        self,
        *,
        token: str | SecretStr | None = None,
        url: str | httpx2.URL | None = None,
        http_client: httpx2.AsyncClient | None = None,
        default_params: BaseGeocoderParams | None = None,
        timeout: int | httpx2.Timeout | None = None,
    ) -> None:
        self._check_type(token, (str, SecretStr), "token")
        self._check_type(url, (str, httpx2.URL), "url")
        self._check_type(http_client, httpx2.AsyncClient, "http_client")
        self._check_type(default_params, BaseGeocoderParams, "default_params")
        self._check_type(timeout, (int, float, httpx2.Timeout), "timeout")

        self.__token = self._resolve_token(token)
        self.base_url = self._resolve_url(url)

        self.timeout = timeout if timeout is not None else httpx2.Timeout(60)

        self._default_params = (
            default_params if default_params is not None else BaseGeocoderParams()
        )

        self._owns_client = http_client is None
        self._client = (
            http_client if http_client is not None else self._build_async_client()
        )

    @staticmethod
    def _check_type(
        value: Any,
        expected: type | tuple[type, ...],
        name: str,
    ) -> None:
        if value is None or isinstance(value, expected):
            return

        expected_name = (
            expected.__name__
            if isinstance(expected, type)
            else " | ".join(t.__name__ for t in expected)
        )
        raise TypeError(
            f"Invalid `{name}` argument; "
            f"expected `{expected_name}`, got {type(value).__name__}."
        )

    def _resolve_token(
        self,
        token: str | SecretStr | None,
    ) -> SecretStr:

        if token is None:
            try:
                token = os.environ[YANDEX_API_KEY]
            except KeyError as exc:
                raise TokenNotFoundError(
                    "API token is required. "
                    "Pass it explicitly via `token=` or "
                    f"set the `{YANDEX_API_KEY}` environment variable."
                ) from exc

        if isinstance(token, SecretStr):
            return token

        return SecretStr(token)

    def _resolve_url(self, url: str | httpx2.URL | None) -> httpx2.URL:
        if url is None:
            try:
                url = os.environ[YANDEX_BASE_URL]
            except KeyError:
                url = self._YANDEX_GEOCODER_URL
                logger.info(
                    "`base_url` not provided and %s env var not set; using default: %s",
                    YANDEX_BASE_URL,
                    self._YANDEX_GEOCODER_URL,
                )
        return self._enforce_trailing_slash(url)

    # copied from anthropic-sdk-python
    def _enforce_trailing_slash(self, url: str | httpx2.URL) -> httpx2.URL:

        if isinstance(url, str):
            url = httpx2.URL(url)

        if url.raw_path.endswith(b"/"):
            return url
        return url.copy_with(raw_path=url.raw_path + b"/")

    @property
    def user_agent(self) -> str:
        return (
            f"{self.__class__.__name__}/Python-{platform.python_version()} "
            f"(api-version={self._YANDEX_GEOCODER_VERSION})"
        )

    @property
    def default_headers(self) -> Mapping[str, str]:
        return {
            "Accept": "application/json",
            "User-Agent": self.user_agent,
        }

    def _build_async_client(self) -> httpx2.AsyncClient:
        return httpx2.AsyncClient(
            timeout=self.timeout,
            headers=self.default_headers,
        )

    def is_closed(self) -> bool:
        return self._client.is_closed

    async def close(self) -> None:
        if self._owns_client:
            await self._client.aclose()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, exc_tb) -> None:
        await self.close()

    def _make_status_error(self, exc: httpx2.HTTPStatusError) -> Exception:
        try:
            error_response = GeocodeErrorResponse.model_validate_json(
                exc.response.content
            )
            error_message = error_response.message
        except (ValidationError, ValueError):
            error_message = exc.response.text or str(exc)

        status_code = exc.response.status_code

        match status_code:
            case 400:
                return BadRequestError(error_message)
            case 401:
                return UnauthorizedError(error_message)
            case 403:
                return ForbiddenError(error_message)
            case 429:
                return RateLimitError(error_message)
            case _:
                # Fallback
                return RequestError(f"HTTP {status_code}: {error_message}")

    def _prepare_params(
        self,
        *,
        model: type[P],
        geocode: str | None,
        params: P | None,
        kwargs: dict[str, Any],
    ) -> dict[str, Any]:

        if params is not None:
            if not isinstance(params, model):
                raise TypeError(
                    f"Expected {model.__name__}, got {type(params).__name__}"
                )
            if geocode is not None or kwargs:
                raise TypeError(
                    "`params` cannot be combined with `geocode` or keyword arguments."
                )

            request = params

        else:
            if geocode is None:
                raise TypeError("`geocode` is required.")

            data = (
                self._default_params.model_dump(exclude_none=True)
                | kwargs
                | {"geocode": geocode}
            )
            try:
                request = model.model_validate(data)
            except ValidationError as exc:
                message = handle_query_exception(exc)
                raise InvalidParamsError(message) from exc

        query = request.to_query_params()

        return query | {"apikey": self.__token.get_secret_value()}

    async def _request(
        self,
        params: Mapping[str, Any],
    ) -> dict[str, Any]:
        response = await self._client.get(
            url=self.base_url,
            params=params,
        )

        try:
            response.raise_for_status()
        except httpx2.HTTPStatusError as exc:
            raise self._make_status_error(exc) from exc

        return response.json()

    async def _execute(
        self,
        *,
        model: type[P],
        geocode: str | None,
        params: P | None,
        kwargs: dict[str, Any],
    ) -> GeocodeResponse:
        query = self._prepare_params(
            model=model,
            geocode=geocode,
            params=params,
            kwargs=kwargs,
        )

        raw_data = await self._request(query)

        try:
            return GeocodeResponse.model_validate(raw_data)
        except ValidationError as exc:
            message = handle_query_exception(exc)
            raise UnexpectedResponseError(message) from exc

    @overload
    async def geocode(
        self,
        geocode: str,
        **kwargs: Unpack[ForwardKwargs],
    ) -> GeocodeResponse: ...

    @overload
    async def geocode(
        self,
        *,
        params: ForwardGeocoderParams,
    ) -> GeocodeResponse: ...

    async def geocode(
        self,
        geocode: str | None = None,
        *,
        params: ForwardGeocoderParams | None = None,
        **kwargs: Unpack[ForwardKwargs],
    ) -> GeocodeResponse:
        return await self._execute(
            model=ForwardGeocoderParams,
            geocode=geocode,
            params=params,
            kwargs=kwargs,
        )

    @overload
    async def reverse_geocode(
        self,
        coordinates: str,
        **kwargs: Unpack[ReverseKwargs],
    ) -> GeocodeResponse: ...

    @overload
    async def reverse_geocode(
        self,
        *,
        params: ReverseGeocoderParams,
    ) -> GeocodeResponse: ...

    async def reverse_geocode(
        self,
        coordinates: str | None = None,
        *,
        params: ReverseGeocoderParams | None = None,
        **kwargs: Unpack[ReverseKwargs],
    ) -> GeocodeResponse:
        return await self._execute(
            model=ReverseGeocoderParams,
            geocode=coordinates,
            params=params,
            kwargs=kwargs,
        )

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"token=***, "
            f"url={self.base_url!r}, "
            f"timeout={self.timeout!r}, "
            f"owns_client={self._owns_client!r})"
        )
