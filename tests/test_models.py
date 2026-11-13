import pytest
from pydantic import ValidationError
from ..src.models import Zone, ZoneType, Connection, Drone, Graph


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


def test_connection():
    con = Connection(zones=["hub1", "hub2"], max_link_capacity=2)
    assert con.max_link_capacity == 2


def test_invalid_zones_connection():
    with pytest.raises(ValidationError):
        print("invalid_zone_connection")
        Connection(zones=["hub1"], max_link_capacity=2)


def test_invalid_capacity_connection():
    with pytest.raises(ValidationError):
        print("invalid_capacity_connection")
        Connection(zones=["hub1", "hub2"], max_link_capacity=-1)


def test_drone_defaults():
    drone = Drone(id=1, current_zone="start")
    assert drone.id == 1
    assert drone.current_zone == "start"
    assert drone.target_zone is None
    assert drone.remaining_turns == 0
    assert drone.has_reached_end is False


def test_drone_in_transit():
    drone = Drone(
        id=2,
        current_zone="start",
        target_zone="restricted_roof",
        remaining_turns=2,
    )
    assert drone.target_zone == "restricted_roof"
    assert drone.remaining_turns == 2


def test_invalid_drone_id():
    with pytest.raises(ValidationError):
        Drone(id=0, current_zone="start")


def test_invalid_drone_remaining_turns():
    with pytest.raises(ValidationError):
        Drone(id=1, current_zone="start", remaining_turns=-1)


def test_graph_creation_and_neighbors():
    z_start = Zone(name="start", x=0, y=0, is_start=True)
    hub1 = Zone(name="hub1", x=1, y=0)
    z_end = Zone(name="end", x=2, y=0, is_end=True)

    test_con1 = Connection(zones=["start", "hub1"], current_drones_count=1)
    test_con2 = Connection(zones=["hub1", "end"], current_drones_count=1)

    graph = Graph(
        zones={"start": z_start, "hub1": hub1, "end": z_end},
        connections=[test_con1, test_con2],
        start_zone_name="start",
        end_zone_name="end",
    )

    assert graph.start_zone_name == "start"
    assert graph.end_zone_name == "end"
    assert graph.get_neighbors("hub1") == ["start", "end"]

# Graph.model_rebuild()
