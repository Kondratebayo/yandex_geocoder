from pydantic import BaseModel, ConfigDict
from pydantic_extra_types.coordinate import Latitude, Longitude


class Point(BaseModel):
    model_config = ConfigDict(frozen=True)
    
    lat: Latitude
    lon: Longitude


class BoundingBox(BaseModel):
    model_config = ConfigDict(frozen=True)
    
    lower: Point
    upper: Point
