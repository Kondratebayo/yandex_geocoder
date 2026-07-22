from __future__ import annotations

import logging
from collections.abc import Sequence
from typing import Literal, Self, TypedDict

from pydantic import BaseModel, Field, field_serializer, model_validator
from pydantic.v1 import ConfigDict
from pydantic_extra_types.coordinate import Latitude, Longitude

from yandex_geocoder.enums import KindEnum, LangEnum

logger = logging.getLogger(__name__)


LonLat = Sequence[Longitude, Latitude]
"""A geographic coordinate represented as (longitude, latitude)."""

Span = Sequence[float, float]

BBox = Sequence[LonLat, LonLat]
"""Bounding box represented by two corner coordinates."""


class CommonKwargs(TypedDict, total=False):
    lang: LangEnum | str
    ll: LonLat
    spn: Span
    results: int
    skip: int


class ForwardKwargs(CommonKwargs, total=False):
    rspn: bool
    bbox: BBox


class ReverseKwargs(CommonKwargs, total=False):
    sco: Literal['longlat', 'latlong']
    kind: KindEnum


class BaseGeocoderParams(BaseModel):
    model_config = ConfigDict(extra='forbid', )
    geocode: str | None = None
    lang: LangEnum = LangEnum.RU
    ll: LonLat | None = None
    spn: Span | None = None
    response_format: Literal['json'] = Field(
        default='json',
        serialization_alias='format',
    )
    results: int = Field(default=10, ge=1, le=50)
    skip: int = Field(default=0, ge=0)

    @field_serializer('ll', when_used='json-unless-none')
    def serialize_ll(self, ll: LonLat) -> str:
        lon, lat = ll
        return f'{lon},{lat}'

    @field_serializer('spn', when_used='json-unless-none')
    def serialize_span(self, span: Span) -> str:
        delta_lon, dela_lat = span
        return f'{delta_lon},{dela_lat}'


    @model_validator(mode='after')
    def validate_skip_field(self) -> Self:
        if self.skip == 0:
            return self
        
        if self.skip % self.results != 0:
            raise ValueError(
                'The skip value must be evenly divisible by the results value: '
                f'{self.skip} % {self.results} != 0'
            )

        return self

    def to_query_params(self) -> dict[str, str | int]:
        return self.model_dump(mode='json', by_alias=True, exclude_none=True)


class ForwardGeocoderParams(BaseGeocoderParams):
    geocode: str
    rspn: bool = Field(default=False)
    bbox: BBox | None = None

    @field_serializer('rspn', when_used='json')
    def serialize_rspn(self, rspn: bool) -> int:
        return int(rspn)

    @field_serializer('bbox', when_used='json-unless-none')
    def serialize_bbox(self, v: BBox) -> str:
        p1, p2 = v
        return (
            f'{p1[0]},{p1[1]}~{p2[0]},{p2[1]}'
            )

    @model_validator(mode='after')
    def bbox_warning(self) -> Self:
        if self.bbox and (self.ll and self.spn):
            logger.warning(
                'If you use both bbox and ll+spn parameters at the same time, '
                'bbox will take precedence.'
            )
        return self


class ReverseGeocoderParams(BaseGeocoderParams):
    geocode: str
    sco: Literal['longlat', 'latlong'] = 'longlat'
    kind: KindEnum | None = None

    @model_validator(mode='after')
    def spn_ignore_warning(self) -> Self:
        if self.kind is KindEnum.DISTRICT and self.spn is not None:
            logger.warning(
                'if the geocode parameter contains coordinates and the kind parameter is set to district, '
                'the spn parameter is ignored.'
            )
        return self
