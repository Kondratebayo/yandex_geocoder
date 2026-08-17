from pydantic import BaseModel, ConfigDict

from yandex_geocoder.enums import KindEnum
from yandex_geocoder.models.geometry import BoundingBox, Point


class Geocoded(BaseModel):
    model_config = ConfigDict(frozen=True)
    
    name: str
    address: str
    coordinates: Point
    kind: KindEnum | str
    description: str | None = None
    precision: str | None = None
    bounded_by: BoundingBox | None = None


class GeocodeResult(BaseModel):
    """Domain model of response"""
    model_config = ConfigDict(frozen=True)
    
    found: int
    locations: list[Geocoded]
    
    @property
    def first(self) -> Geocoded | None:
        """Return a first Geocoded result ( if it has )

        Returns:
            Geocoded | None
        """        """"""
        return self.locations[0] if self.locations else None
