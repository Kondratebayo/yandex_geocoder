"""
This module needs to correctly represent nested yandex JSON as DTO
and instantly return Domain model to user
"""
from pydantic import AliasPath, BaseModel, Field

from yandex_geocoder.models.domain import Geocoded, GeocodeResult
from yandex_geocoder.models.geometry import BoundingBox, Point


class AddressComponent(BaseModel):
    kind: str
    name: str

class Address(BaseModel):
    country_code: str | None = None
    formatted: str
    components: list[AddressComponent] = Field(default_factory=list, alias="Components")

class GeocoderMetaData(BaseModel):
    kind: str
    precision: str | None = None
    text: str
    address: Address = Field(alias="Address")


class BoundedBy(BaseModel):
    lower_corner: str = Field(validation_alias=AliasPath("Envelope", "lowerCorner"))
    upper_corner: str = Field(validation_alias=AliasPath("Envelope", "upperCorner"))

    def to_domain(self) -> BoundingBox:
        lower_lon, lower_lat = self.lower_corner.split()
        upper_lon, upper_lat = self.upper_corner.split()
        return BoundingBox(
            lower=Point(lon=float(lower_lon), lat=float(lower_lat)), # pyright: ignore
            upper=Point(lon=float(upper_lon), lat=float(upper_lat)), # pyright: ignore
        )

class GeoObject(BaseModel):
    name: str
    description: str | None = None
    uri: str | None = None
    
    metadata: GeocoderMetaData = Field(validation_alias=AliasPath("metaDataProperty", "GeocoderMetaData"))
    pos: str = Field(validation_alias=AliasPath("Point", "pos"))
    bounded_by: BoundedBy | None = Field(default=None, alias="boundedBy")

    def to_domain(self) -> Geocoded:
        lon, lat = self.pos.split()
        return Geocoded(
            name=self.name,
            address=self.metadata.address.formatted,
            coordinates=Point(lon=float(lon), lat=float(lat)), # pyright: ignore
            kind=self.metadata.kind,
            description=self.description,
            precision=self.metadata.precision,
            bounded_by=self.bounded_by.to_domain() if self.bounded_by else None,
        )

class FeatureMember(BaseModel):
    geo_object: GeoObject = Field(alias="GeoObject")

class GeocoderResponseMetaData(BaseModel):
    request: str
    found: int
    results: int
    skip: int = 0
    fix: str | None = None
    suggest: str | None = None
    request_pos: str | None = Field(default=None, validation_alias=AliasPath("Point", "pos"))

class GeoObjectCollection(BaseModel):
    metadata: GeocoderResponseMetaData = Field(
        validation_alias=AliasPath("metaDataProperty", "GeocoderResponseMetaData")
    )
    feature_members: list[FeatureMember] = Field(default_factory=list, alias="featureMember")

class GeocodeResponse(BaseModel):
    """Inner DTO class."""

    collection: GeoObjectCollection = Field(validation_alias=AliasPath("response", "GeoObjectCollection"))

    def to_domain(self) -> GeocodeResult:
        return GeocodeResult(
            found=self.collection.metadata.found,
            locations=[
                member.geo_object.to_domain() 
                for member in self.collection.feature_members
            ]
        )

class GeocodeErrorResponse(BaseModel):
    status_code: int = Field(alias="statusCode")
    error: str
    message: str
