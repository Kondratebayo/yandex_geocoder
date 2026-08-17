# Yandex Geocoder SDK

An asynchronous Python client for the [Yandex Geocoder API](https://yandex.ru/maps-api/products/geocoder-api).

## Features

* Async API based on `httpx2`
* Forward and reverse geocoding
* Pydantic-based request and response validation
* Typed request parameters
* Custom `AsyncClient` support
* Structured exceptions for API and network errors
* Domain models independent from the raw API response

## Installation

```bash
pip install yandex-geocoder
```

## Quick start

```python
from yandex_geocoder import AsyncYandexGeocoderClient

async with AsyncYandexGeocoderClient(token="YOUR_API_KEY") as client:
    result = await client.geocode("Moscow, Red Square")

    print(result.first)
```

Reverse geocoding:

```python
async with AsyncYandexGeocoderClient(token="YOUR_API_KEY") as client:
    result = await client.reverse_geocode("37.6173,55.7558")

    print(result.first)
```

The client can also accept a custom `httpx2.AsyncClient`, which allows connection settings and other HTTP client options to be managed externally.

## Error handling

The SDK provides dedicated exceptions for common errors, including invalid parameters, authentication errors, rate limits, timeouts, network errors, and unexpected API responses.

## Models

API responses are validated with Pydantic DTOs and converted into immutable domain models, so application code does not need to work directly with the nested Yandex API response structure.

The main result model contains the number of found locations and a list of geocoded objects, with a convenient `.first` property for accessing the first result.

## License

MIT
