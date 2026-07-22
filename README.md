# Yandex Geocoder SDK

A lightweight asynchronous Python SDK for the Yandex Geocoder API.

## Features

- Async client built on `httpx2`
- Fully typed API
- Pydantic request and response models
- Automatic request validation
- Convenient forward and reverse geocoding
- Custom exceptions for API and validation errors

## Installation

```bash
pip install yandex-geocoder
```

## Quick start

```python
from yandex_geocoder import YandexGeocoderClient

async with YandexGeocoderClient(token="YOUR_API_KEY") as client:
    response = await client.geocode("Red Square, Moscow")

    first = response.collection.feature_members[0].geo_object

    print(first.name)
    print(first.coordinates)
```

## Forward geocoding

```python
response = await client.geocode(
    "Moscow",
    results=5,
    lang="en_US",
)
```

or with a parameter model:

```python
from yandex_geocoder.models import ForwardGeocoderParams

params = ForwardGeocoderParams(
    geocode="Moscow",
    results=5,
)

response = await client.geocode(params=params)
```

## Reverse geocoding

```python
response = await client.reverse_geocode(
    "37.620393 55.75396"
)
```

or

```python
from yandex_geocoder.models import ReverseGeocoderParams

params = ReverseGeocoderParams(
    geocode="37.620393 55.75396",
)

response = await client.reverse_geocode(params=params)
```

## Response

The SDK returns typed Pydantic models.

```python
geo = response.collection.feature_members[0].geo_object

print(geo.name)
print(geo.description)
print(geo.coordinates)
print(geo.metadata.address.formatted)
```

## Errors

The SDK raises dedicated exceptions instead of raw HTTP errors.

```python
from yandex_geocoder.exceptions import (
    InvalidParamsError,
    UnauthorizedError,
    RateLimitError,
    RequestError,
)

try:
    await client.geocode("Moscow")
except RequestError:
    ...
```

## License

MIT