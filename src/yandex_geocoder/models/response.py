# DTO
from __future__ import annotations

from pydantic import (
    AliasPath,
    BaseModel,
    Field,
)


class AddressComponent(BaseModel):
    kind: str
    name: str


class Address(BaseModel):
    country_code: str | None = None
    formatted: str
    components: list[AddressComponent] = Field(
        default_factory=list, 
        alias="Components"
    )


class GeocoderMetaData(BaseModel):
    kind: str
    precision: str | None = None
    text: str
    address: Address = Field(alias="Address")


class BoundedBy(BaseModel):
    lower_corner: str = Field(validation_alias=AliasPath("Envelope", "lowerCorner"))
    upper_corner: str = Field(validation_alias=AliasPath("Envelope", "upperCorner"))


class GeoObject(BaseModel):
    name: str
    description: str | None = None
    uri: str | None = None
    
    metadata: GeocoderMetaData = Field(
        validation_alias=AliasPath("metaDataProperty", "GeocoderMetaData")
    )
    
    pos: str = Field(validation_alias=AliasPath("Point", "pos"))
    
    bounded_by: BoundedBy | None = Field(default=None, alias="boundedBy")

    @property
    def coordinates(self) -> tuple[float, float]:
        lon, lat = self.pos.split()
        return float(lon), float(lat)


class FeatureMember(BaseModel):
    geo_object: GeoObject = Field(alias="GeoObject")


class GeocoderResponseMetaData(BaseModel):
    request: str
    found: int
    results: int
    skip: int = 0
    fix: str | None = None
    suggest: str | None = None
    
    request_pos: str | None = Field(
        default=None, 
        validation_alias=AliasPath("Point", "pos")
    )


class GeoObjectCollection(BaseModel):
    metadata: GeocoderResponseMetaData = Field(
        validation_alias=AliasPath("metaDataProperty", "GeocoderResponseMetaData")
    )
    feature_members: list[FeatureMember] = Field(
        default_factory=list, 
        alias="featureMember"
    )


class GeocodeResponse(BaseModel):
    collection: GeoObjectCollection = Field(
        validation_alias=AliasPath("response", "GeoObjectCollection")
    )


class GeocodeErrorResponse(BaseModel):
    status_code: int = Field(alias="statusCode")
    error: str
    message: str