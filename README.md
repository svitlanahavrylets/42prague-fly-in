*This project has been created as part of the 42 curriculum by \<shavryle\>.*

## Description

Fly-in routes a fleet of drones from one start hub to one end hub through a
map of connected zones. It searches for a route for each drone, reserves the
planned zones and connections by turn, then prints the simulation. The goal is
to deliver all drones in as few turns as possible while respecting movement
costs and capacities.

The project is written in Python 3.10+ and uses Pydantic models, a custom map
parser, a time-aware A* search, and an optional Pygame visualizer.

## Project Structure

```text
main.py                         CLI entry point
src/
  models/                       Zones, connections, graph, and drones
  parsers/                      CLI arguments and map validation
  algorithms/                   A* route search and reservations
  controllers/                  Turn-by-turn simulation history and output
  visualizers/                  Base visualizer, colors, and Pygame view
maps/                           Easy, medium, hard, and challenger maps
my_maps/                        Local example and invalid maps
tests/                          Pydantic model tests
Makefile                        Install, run, debug, clean, and lint targets
pyproject.toml                  Project metadata and dependencies
```

## Instructions

### Requirements

- Python 3.10 or later.
- [uv](https://docs.astral.sh/uv/) to install dependencies and use the Makefile.
- Pygame mode uses `pygame-ce`, declared in the development dependency group.

### Installation

From the repository root, install the project and its declared dependencies:

```bash
uv sync
```

### Execution

Run a map with the command-line output:

```bash
uv run python -m main maps/easy/01_linear_path.txt --visual cli
```

Open the animated Pygame view instead:

```bash
uv run python -m main maps/easy/01_linear_path.txt --visual pygame
```

The map path is optional. If omitted, the program uses
`my_maps/example.txt`. The visual flag accepts `cli` or `pygame` and defaults
to `cli`.

The equivalent Makefile form is:

```bash
make run FILE=maps/easy/01_linear_path.txt ARGS="--visual pygame"
```

### Map Format & Validation Rules

The first map directive is `nb_drones: <positive_integer>`. Blank lines and
text after `#` are ignored, so comments may appear before the drone count.
The count must appear before any zone or connection definition.

```text
nb_drones: 2
start_hub: start 0 0 [color=green]
hub: relay 1 0 [zone=normal color=blue max_drones=2]
end_hub: goal 2 0 [color=red]
connection: start-relay [max_link_capacity=2]
connection: relay-goal
```

| Zone type | Cost to enter | Behavior in this implementation |
| --- | ---: | --- |
| `normal` | 1 turn | Standard zone; capacity defaults to 1. |
| `priority` | 1 turn | Receives a small A* score bonus when selected as the next zone. |
| `restricted` | 2 turns | The drone is represented on the connection during transit, then arrives. |
| `blocked` | — | Excluded from neighbor lists, so drones cannot enter it. |

Validation performed by the parser includes:

- A positive drone count before map definitions, with duplicate definitions
  rejected.
- Exactly one start hub and one end hub; zone names must be unique.
- Integer coordinates. Zone names are single tokens and cannot contain `-`.
- Connections may refer only to zones already defined. Self-links and duplicate
  undirected connections are rejected.
- Zone metadata supports `zone`, `color`, and `max_drones`; connection
  metadata supports `max_link_capacity`. Capacities must be positive integers.
- Zone types must be `normal`, `priority`, `restricted`, or `blocked`.

`max_drones` defaults to 1. The scheduler treats start and end hubs as
unlimited-capacity zones; any supplied `max_drones` value is still parsed and
validated. Link capacity defaults to 1. Colors are not validated by the map
parser. In Pygame mode, unsupported colors used for non-blocked hubs fall back
to the default hub color; blocked hubs use a fixed dark fill.

## Architecture & Algorithm Strategy

### ASCII Pipeline

```text
            Map file + CLI arguments
                      |
                      v
                  MapParser
                      |
               Graph + drone count
                 /           \
                v             v
       CollisionManager   Drone.create_fleet
                \             /
                 v           v
               CooperativeAStar
             plan each drone in order
             reserve each found route
                      |
                      v
             SimulationController
               snapshots + output
                      |
              CLI text or Pygame view
```

### Space-Time Cooperative A\*

`CooperativeAStar` searches states identified by `(zone, turn)`. A heap orders
states by their A* score. From a state, the search can wait one turn in the
current zone or move to an accessible neighbor. It stops when the destination
is reached or the configured search horizon is reached (1,000 turns by
default).

Routes are planned sequentially in drone ID order. After each route is found,
`CollisionManager` reserves it before the next drone is planned. This is a
prioritized, single-drone-search approach, not a joint search over all drone
routes.

### Heuristic & Zone Costs

The planner adds elapsed movement and waiting turns to `g`. Its heuristic is a
BFS distance table computed once from the end hub. The table counts graph hops
and ignores their different turn costs and reservations. Entering a restricted
zone costs two turns; entering other accessible zones costs one. Blocked zones
are omitted. Entering a priority zone lowers that neighbor's `f` score by
`0.001`; this is a small local preference, not a guarantee that every route
will visit a priority zone.

### Collision & Capacity Scheduling

- Zone reservations are keyed by zone and turn; link reservations are keyed by
  the undirected connection and turn.
- The planner checks destination-zone capacity and every turn of a connection
  traversal before adding a move.
- Waiting is an option when the current zone remains available on the next
  turn.
- Start and end hubs are unlimited in the reservation manager. Other zones use
  `max_drones`; connections use `max_link_capacity`.
- A restricted move reserves its connection for both turns and records the
  in-flight connection state for the intermediate turn.

### Complexity & Trade-offs

Let `V` be the number of zones, `E` the number of connections, `T` the search
horizon, and `K` the number of drones. The BFS distance-table setup takes
`O(VE)` time in this implementation because neighbor lookup scans the
connection list, and stores `O(V)` distances. For one drone, at most `O(VT)`
distinct `(zone, turn)` states can be expanded. Neighbor lookup scans up to
`E` connections, and the heap can contain repeated candidate states. A broad
upper bound for search and heap work is `O(VTE log(VTE))` per drone. Search
entries also hold copied paths. In a broad worst case, copying paths can add
`O(VT^2E)` time and queue memory per drone. Sequential planning repeats the
search for each drone and makes later routes depend on earlier reservations;
it does not guarantee the globally smallest fleet completion time.

## Simulation Output & Visual Feedback

The CLI prints space-separated movements for each non-empty turn. Stationary
drones are omitted, and restricted transit is printed with the connection
name. The output does not include turn numbers or blank lines for turns with
no movement.

This example is from `maps/easy/01_linear_path.txt`:

```text
nb_drones: 2

start_hub: start 0 0 [color=green]
hub: waypoint1 1 0 [color=blue]
hub: waypoint2 2 0 [color=blue]
end_hub: goal 3 0 [color=red]

connection: start-waypoint1
connection: waypoint1-waypoint2
connection: waypoint2-goal
```

Exact CLI output for this map (`--visual cli`):

```text
D1-waypoint1
D1-waypoint2 D2-waypoint1
D1-goal D2-waypoint2
D2-goal
```

These are turns 1 through 4, in order.

Pygame displays the map, connection graph, drone IDs, zone labels, and zone
occupancy (`current/capacity`; start and end show `current/∞`). It animates
movement, shows `1/2` and `2/2` progress on restricted transits, and provides a
zone-type legend and turn/delivery status. The window can be resized.

- `SPACE`: pause or play
- `LEFT` / `RIGHT`: step between turns
- `UP` / `DOWN`: change playback speed
- `R`: restart
- `ESC`: quit

## Useful Commands

| Command | Makefile behavior |
| --- | --- |
| `make install` | Run `uv sync`. |
| `make run` | Run `main` with `my_maps/example.txt` and CLI output by default. |
| `make run FILE=... ARGS="..."` | Set the map path and pass CLI flags. |
| `make debug` | Start `pdb` on `main.py` with the default map. `FILE` and `ARGS` can be set as for `make run`. |
| `make lint` | Run Flake8 and the configured non-strict mypy checks. |
| `make lint-strict` | Run Flake8 and `mypy --strict`. |
| `make clean` | Remove the listed Python caches, `build/`, and `dist/`. |
| `make fclean` | Run `clean`, then remove `.venv` and `uv.lock`. |
| `make all` | Run the `install` target. |
| `make bonus` | Print that no bonus target is implemented. |

## Resources

- Local subject transcription: `docs/fly-in-subject.md`. It is gitignored and
  is not included in the repository checkout shared for evaluation.
- [`maps/`](maps/) — sample easy, medium, and hard maps, plus the optional
  challenger map.
- [Cooperative Pathfinding, David Silver](https://davidstarsilver.wordpress.com/wp-content/uploads/2025/05/aiide-05.pdf)
  — background on cooperative multi-agent path planning.

## AI Usage

AI tools were used to support debugging, code explanations, and documentation.
Generated suggestions are not treated as authoritative: the project author is
responsible for checking them against the subject and implementation, and for
understanding and validating all submitted work. The subject also recommends
critical review and peer feedback.
