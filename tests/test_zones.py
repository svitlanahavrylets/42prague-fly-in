import pytest
from pydantic import ValidationError
from src.models import Zone, ZoneType


def test_zone_defaults():
    zone = Zone(name="hub1", x=10, y=20)
    assert zone.name == "hub1"
    assert zone.zone_type == ZoneType.NORMAL
    assert zone.max_drones == 1
    assert zone.color is None


def test_invalid_max_drones():
    with pytest.raises(ValidationError):
        print("invalid_max_drones")
        Zone(name="bad_hub", x=0, y=0, max_drones=-1)


def test_invalid_zone_type():
    with pytest.raises(ValidationError):
        print("invalid_zone_type")
        Zone(name="bad_hub", x=0, y=0, zone_type="unknown")

