import pytest
from pydantic import ValidationError
from src.models import Zone, ZoneType, Connection, Drone, Graph


def test_zone_defaults() -> None:
    """Check the default values for a zone."""
    zone = Zone(
        name="hub1",
        x=10,
        y=20,
        zone_type=ZoneType.NORMAL,
    )
    assert zone.name == "hub1"
    assert zone.zone_type == ZoneType.NORMAL
    assert zone.max_drones == 1
    assert zone.color is None


def test_invalid_max_drones() -> None:
    """Check that a zone rejects a negative capacity."""
    with pytest.raises(ValidationError):
        Zone(
            name="bad_hub",
            x=0,
            y=0,
            zone_type=ZoneType.NORMAL,
            max_drones=-1,
        )


def test_invalid_zone_type() -> None:
    """Check that a zone rejects an unknown type."""
    with pytest.raises(ValidationError):
        Zone.model_validate(
            {
                "name": "bad_hub",
                "x": 0,
                "y": 0,
                "zone_type": "unknown",
            }
        )


def test_connection() -> None:
    """Check that a connection stores its capacity."""
    con = Connection(zones=("hub1", "hub2"), max_link_capacity=2)
    assert con.max_link_capacity == 2


def test_invalid_zones_connection() -> None:
    """Check that a connection requires two zone names."""
    with pytest.raises(ValidationError):
        Connection.model_validate(
            {"zones": ["hub1"], "max_link_capacity": 2}
        )


def test_invalid_capacity_connection() -> None:
    """Check that a connection rejects a negative capacity."""
    with pytest.raises(ValidationError):
        Connection(zones=("hub1", "hub2"), max_link_capacity=-1)


def test_drone_defaults() -> None:
    """Check the default values for a drone."""
    drone = Drone(id=1, current_zone="start")
    assert drone.id == 1
    assert drone.current_zone == "start"


def test_invalid_drone_id() -> None:
    """Check that a drone ID must be positive."""
    with pytest.raises(ValidationError):
        Drone(id=0, current_zone="start")


def test_graph_creation_and_neighbors() -> None:
    """Check graph endpoints and neighbor lookup."""
    z_start = Zone(
        name="start",
        x=0,
        y=0,
        zone_type=ZoneType.NORMAL,
        is_start=True,
    )
    hub1 = Zone(
        name="hub1",
        x=1,
        y=0,
        zone_type=ZoneType.NORMAL,
    )
    z_end = Zone(
        name="end",
        x=2,
        y=0,
        zone_type=ZoneType.NORMAL,
        is_end=True,
    )

    test_con1 = Connection(
        zones=("start", "hub1")
    )
    test_con2 = Connection(
        zones=("hub1", "end")
    )

    graph = Graph(
        zones={"start": z_start, "hub1": hub1, "end": z_end},
        connections=[test_con1, test_con2],
        start_zone_name="start",
        end_zone_name="end",
    )

    assert graph.start_zone_name == "start"
    assert graph.end_zone_name == "end"
    neighbors = graph.get_neighbors("hub1")
    assert [zone.name for zone, _, _ in neighbors] == ["start", "end"]

# Graph.model_rebuild()
