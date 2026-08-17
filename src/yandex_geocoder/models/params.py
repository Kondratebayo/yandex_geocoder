from __future__ import annotations

import logging
from typing import Any, Literal, Self, TypedDict

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_serializer,
    field_validator,
    model_validator,
)

from yandex_geocoder.enums import KindEnum, LangEnum
from yandex_geocoder.models.geometry import BoundingBox, Point

logger = logging.getLogger(__name__)

Span = tuple[float, float]


class CommonKwargs(TypedDict, total=False):
    lang: LangEnum | str
    ll: Point
    spn: Span
    results: int
    skip: int


class ForwardKwargs(CommonKwargs, total=False):
    rspn: bool
    bbox: BoundingBox


class ReverseKwargs(CommonKwargs, total=False):
    sco: Literal['longlat', 'latlong']
    kind: KindEnum


class BaseGeocoderParams(BaseModel):
    model_config = ConfigDict(extra='forbid', )
    geocode: str | None
    lang: LangEnum = LangEnum.RU
    ll: Point | None = None
    spn: Span | None = None
    response_format: Literal['json'] = Field(
        default='json',
        serialization_alias='format',
    )
    results: int = Field(default=10, ge=1, le=50)
    skip: int = Field(default=0, ge=0)

    @field_serializer('ll', when_used='json-unless-none')
    def serialize_ll(self, ll: Point) -> str:
        return f'{ll.lon},{ll.lat}'

    @field_serializer('spn', when_used='json-unless-none')
    def serialize_span(self, span: Span) -> str:
        delta_lon, dela_lat = span
        return f'{delta_lon},{dela_lat}'

    @field_validator('ll', mode='before')
    @classmethod
    def _parse_tuple_to_point(cls, ll: Any) -> Any:
        if isinstance(ll, (tuple, list)) and len(ll) == 2:
            return Point(lon=float(ll[0]), lat=float(ll[1])) # pyright: ignore
        return ll

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
    bbox: BoundingBox | None = None

    @field_serializer('rspn', when_used='json')
    def serialize_rspn(self, rspn: bool) -> int:
        return int(rspn)

    @field_serializer('bbox', when_used='json-unless-none')
    def serialize_bbox(self, bbox: BoundingBox) -> str:
        return (
            f'{bbox.lower.lon},{bbox.lower.lat}~{bbox.upper.lon},{bbox.upper.lat}'
            )

    @field_validator('bbox', mode='before')
    @classmethod
    def _parse_tuple_to_bbox(cls, bbox: Any) -> Any:
        if (
            isinstance(bbox, (tuple, list))
            and len(bbox) == 2
            and isinstance(bbox[0], (tuple, list))
            and isinstance(bbox[1], (tuple, list))
        ):
            return BoundingBox(
                lower=Point(lon=float(bbox[0][0]), lat=float(bbox[0][1])), # pyright: ignore
                upper=Point(lon=float(bbox[1][0]), lat=float(bbox[1][1])), # pyright: ignore
            )
        
        return bbox

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
