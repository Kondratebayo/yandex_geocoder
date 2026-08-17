from __future__ import annotations

from enum import StrEnum


class LangEnum(StrEnum):
    """Response language and regional map features.

    Mandatory parameter.

    Attributes:
        RU: Russian (``ru_RU``).
        UA: Ukrainian (``uk_UA``).
        BY: Belarusian (``be_BY``).
        EN_RU: English response, Russian map specifics (``en_RU``).
        EN_US: English response, US map specifics (``en_US``).
        TR: Turkish, Turkey map only (``tr_TR``).
    """

    RU = "ru_RU"
    UA = "uk_UA"
    BY = "be_BY"
    EN_RU = "en_RU"
    EN_US = "en_US"
    TR = "tr_TR"


class KindEnum(StrEnum):
    """Type of the required toponym.

    Only applies if coordinates (not an address) are passed in the
    ``geocode`` parameter. If omitted, the API selects the toponym
    type automatically.

    Attributes:
        HOUSE: A building.
        STREET: A street.
        METRO: A metro station.
        DISTRICT: A city district.
        LOCALITY: A populated place (city/town/village).
    """

    HOUSE = "house"
    STREET = "street"
    METRO = "metro"
    DISTRICT = "district"
    LOCALITY = "locality"