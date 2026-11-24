*This project has been created as part of the 42 curriculum by \<shavryle\>.*

# Fly-in

## Description

Fly-in is a Python drone-routing simulation. It reads a map of zones and
connections, then plans routes from one start hub to one end hub. The drones
move turn by turn, and the simulation checks zone limits, connection limits,
and movement costs. Its goal is to deliver every drone in as few turns as
possible.

Fly-in has a command-line view and an optional animated Pygame view. It uses
Pydantic models, a map parser, Cooperative Space-Time A*, and a reservation
system to plan and display the movement of each drone.

## Project Structure

```text
fly-in/
├── main.py                         CLI entry point
├── pyproject.toml                  Project metadata and dependencies
├── uv.lock                         Locked dependency versions
├── Makefile                        Install, run, debug, clean, and lint
├── README.md                       Project guide
├── assets/
│   └── drone_img.png               Image for drone reprezentation in vizualization
├── maps/
│   ├── easy/                       Basic maps
│   ├── medium/                     Maps with more route choices
│   ├── hard/                       Larger and more restricted maps
│   └── challenger/                 Optional challenge map
├── my_maps/
│   ├── example.txt                 Default example map
│   └── invalid_maps/               Maps used for parser checks
├── src/
│   ├── models/                     Zone, connection, graph, and drone models
│   ├── parsers/                    Command-line and map parsers
│   ├── algorithms/                 Cooperative Space-Time A* and reservations
│   ├── controllers/                Simulation history and CLI output
│   └── visualizers/                Colors and Pygame visualization
└── tests/                          Automated tests
```

## Installation

From the project folder, install the dependencies with:

```bash
make install
```

This command runs `uv sync`. You need Python 3.10 or later and [uv](https://docs.astral.sh/uv/).
The optional Pygame view uses `pygame-ce`, which is listed in the project
dependencies.

## Execution

Run the default map, `my_maps/example.txt`, with:

```bash
make run
```

The command prints the drone movements in the terminal. To open the animated
Pygame view instead, run:

```bash
make run ARGS="--visual pygame"
```

You can select another map with `FILE`:

```bash
make run FILE=maps/easy/01_linear_path.txt
```

You can also run the program directly with Python. The map path is optional;
when it is left out, Fly-in uses `my_maps/example.txt`.

```bash
uv run python -m main
uv run python -m main --visual pygame
uv run python -m main maps/easy/01_linear_path.txt --visual cli
```

## Development & Linting

The Makefile provides common development commands:

| Command | What it does |
|:---|:---|
| `make install` | Installs or updates project dependencies with `uv sync`. |
| `make run` | Runs the default map in the terminal. |
| `make run FILE=... ARGS="..."` | Runs a selected map and passes extra CLI options. |
| `make debug` | Starts Python's debugger with the default map. |
| `make lint` | Runs Flake8 and the configured Mypy checks. |
| `make lint-strict` | Runs Flake8 and strict Mypy checks. |
| `make clean` | Removes configured cache folders and build output. |
| `make fclean` | Runs `clean` and removes the virtual environment. |

Run the recommended checks with:

```bash
make lint-strict
```

## Map Format & Validation Rules

Maps contain a drone count, zone definitions, and connection definitions.
Blank lines and comments that start with `#` are ignored. The default map is
shown below:

```text
nb_drones: 5
start_hub: hub 0 0 [color=green]
end_hub: goal 10 10 [color=yellow]
hub: roof1 3 4 [zone=restricted color=red]
hub: roof2 6 2 [zone=normal color=blue]
hub: corridorA 4 3 [zone=priority color=green max_drones=2]
hub: tunnelB 7 4 [zone=normal color=red]
hub: obstacleX 5 5 [zone=blocked color=gray]
connection: hub-roof1
connection: hub-corridorA
connection: roof1-roof2
connection: roof2-goal
connection: corridorA-tunnelB [max_link_capacity=2]
connection: tunnelB-goal
```

| Map item | Format | Rules |
|:---|:---|:---|
| Drone count | `nb_drones: 5` | Must be a positive integer and appear before zones and connections. |
| Start hub | `start_hub: name x y` | Exactly one is required. It can hold all drones. |
| End hub | `end_hub: name x y` | Exactly one is required. It can receive all drones. |
| Normal zone | `hub: name x y [zone=normal]` | Takes one turn to enter. Capacity defaults to 1. |
| Priority zone | `hub: name x y [zone=priority]` | Takes one turn to enter and gets a small search preference. |
| Restricted zone | `hub: name x y [zone=restricted]` | Takes two turns to enter. The drone must arrive on the next turn. |
| Blocked zone | `hub: name x y [zone=blocked]` | Drones cannot enter or pass through it. |
| Connection | `connection: zoneA-zoneB` | Connects two existing zones in both directions. Capacity defaults to 1. |
| Optional capacity | `max_drones=2` or `max_link_capacity=2` | Must be a positive integer. Hub capacities are ignored for start and end. |
| Optional color | `color=green` | Used by the Pygame view. An unsupported color uses a default color. |

Zone names must be unique, contain no spaces, and cannot contain `-`.
Coordinates must be integers. Connections must refer to zones that were
defined earlier. The parser rejects self-connections and duplicate
connections, even if their zone order is reversed.

## Architecture & Algorithm Strategy

### Program flow

```text
┌────────────────────────────┐
│ Map file and CLI options   │
└─────────────┬──────────────┘
              │
              ▼
┌────────────────────────────┐
│ MapParser                  │
│ Read and validate the map  │
└─────────────┬──────────────┘
              │ Graph + drone count
              ▼
┌────────────────────────────┐
│ Create drones and prepare  │
│ capacity reservations      │
└─────────────┬──────────────┘
              ▼
┌────────────────────────────┐
│ CooperativeAStar           │
│ Plan one route per drone   │
└─────────────┬──────────────┘
              │ Reserve each route
              ▼
┌────────────────────────────┐
│ SimulationController       │
│ Build turn snapshots       │
└─────────────┬──────────────┘
              ▼
┌────────────────────────────┐
│ Terminal output or Pygame  │
└────────────────────────────┘
```

### Why Cooperative Space-Time A* is used

Cooperative Space-Time A* combines the cost already paid with an estimate of
the cost left. Its search states include both a zone and a turn. This matters
because a zone or connection can be free on one turn and reserved on another.
This is the “space-time” part of the name. The “cooperative” part means that
each drone's route is reserved before the next drone is planned. The heuristic
helps the search focus on routes that move toward the end hub.

Fly-in plans routes one drone at a time. After it finds a route, the program
reserves the zones and connections used by that route. The next drone then
searches with those reservations in place. This makes the routes cooperate
and helps prevent collisions. It is a practical, prioritized approach, but it
does not guarantee the globally shortest schedule for the whole fleet.

### BFS heuristic

Before route planning, `_calculate_static_distances()` runs Breadth-First
Search (BFS) from the end hub. It uses a `deque` as a first-in, first-out
queue. For each reachable zone, it stores the number of connections to the
end hub. Blocked zones are skipped by `Graph.get_neighbors()`.

This distance table is the heuristic `h`. It counts each connection as one
step, so it does not include the extra turn for restricted zones, waiting, or
capacity delays. It is a quick estimate that guides the search. If the start
hub is missing from the table, the end hub cannot be reached and route
planning stops with an error.

### Search states and variables

The search state is represented by the zone and turn. Reaching the same zone
on different turns is treated as a different state because other drones may
reserve that zone or its connections at specific turns.

| Variable | Meaning |
|:---|:---|
| `current_zone` | Zone where this search state is located. |
| `turn` | Turn number for the current state. |
| `path` | Planned sequence of `(zone, turn)` steps for this drone. |
| `g_cost` | Turns already spent, including waiting and restricted movement. |
| `_heuristic(zone)` | BFS estimate of the remaining distance to the end hub. |
| `f_score` | Search priority: `g_cost + heuristic`, with a small priority-zone bonus. |
| `open_set` | `heapq` min-heap of states waiting to be explored. |
| `count` | Increasing tie-breaker so heap entries have a stable order. |
| `visited` | Set of `(zone, turn)` states already expanded. |
| `max_turns` | Search limit; it is 1,000 turns by default. |
| `arrival_turn` | Turn when a move reaches the next zone. |
| `is_zone_free` | Whether the destination zone has capacity at arrival. |
| `is_link_free` | Whether the connection has capacity for every turn of the move. |

From each state, Cooperative Space-Time A* can wait one turn if the current
zone remains available, or move to a neighbor if the destination and
connection have capacity. A move into a restricted zone costs two turns and
reserves the connection for both turns. The drone is shown on that connection
during the intermediate turn.

### Priority Queue (`heapq`)

The open set uses Python's `heapq` module, which is a min-heap. Each entry is
a tuple:

```text
(f_score, count, g_cost, turn, zone, path)
```

`heappop()` removes the entry with the lowest `f_score`; `heappush()` adds a
new entry. Both operations take `O(log N)` time, where `N` is the number of
entries currently in the heap. `count` is a unique counter used when two
entries have the same score. This also prevents Python from needing to
compare their zone names or full paths to break a tie.

The current code stores tuples directly. It does not define a `TemporalState`
dataclass, so `heapq` compares the tuple fields in order.

### Capacity and movement rules

`CollisionManager` stores reservations by zone and turn, and by connection
and turn. Start and end hubs have unlimited capacity. Other zones use
`max_drones`, and each connection uses `max_link_capacity`. Drones may wait
when the current zone has space on the next turn. This allows the planner to
avoid a busy zone or connection by choosing a later time.

Priority zones receive a small `0.001` adjustment to their search score. This
is a preference during route selection.

## Simulation Output

The terminal prints one line for each turn that has movement. Each item has
the form `D<ID>-<zone>`. Stationary drones are not printed. During a
restricted move, the drone's location is shown as `D<ID>-<connection>` for
the intermediate turn.

This output is from the default map, `my_maps/example.txt`:

```text
D1-corridorA D3-hub-roof1
D1-tunnelB D2-corridorA D3-roof1
D1-goal D2-tunnelB D3-roof2 D4-corridorA
D2-goal D3-goal D4-tunnelB D5-corridorA
D4-goal D5-tunnelB
D5-goal
```

The program prints only movement lines, so the first line represents turn 1.
Turns with no movement do not produce an empty line.

## Visual Representation

The optional Pygame view shows the map as a graph: circles represent zones
and lines represent connections. Colors mark start, end, priority, restricted,
and blocked zones. Drone IDs move along their planned routes. Zone names and
occupancy counts appear when the pointer is over a zone. Start and end
occupancy is shown against the drone count from the map. Restricted movement
shows its current phase, such as `1/2` or `2/2`.

The window can be resized. The graph coordinates and information panels adapt
to the new window size.

| Key | Action |
|:---|:---|
| `SPACE` | Pause or play the animation. |
| `LEFT` / `RIGHT` | Step to the previous or next turn. |
| `UP` / `DOWN` | Increase or decrease playback speed. |
| `R` | Restart the animation. |
| `ESC` | Close the visualizer. |

## Resources

- [Python documentation](https://docs.python.org/3/)
- [W3Schools Python reference](https://www.w3schools.com/python/python_reference.asp)
- [Python `heapq` module guide](https://www.geeksforgeeks.org/python/heap-queue-or-heapq-in-python/)
- [Pygame documentation](https://www.pygame.org/docs/)
- [Cooperative Pathfinding, David Silver](https://davidstarsilver.wordpress.com/wp-content/uploads/2025/05/aiide-05.pdf)
- [`maps/`](maps/) — easy, medium, hard, and optional challenger maps.

## AI Usage

AI assistants (such as Codex / Gemini) were used during the development of this project for the following tasks:
* **Algorithm Comprehension & Design:** AI helped clarify Cooperative Space-Time A* pathfinding, including `(zone, turn)` states and a reverse BFS distance heuristic. 
* **Debugging & Edge Cases:** Assisting in identifying and resolving edge cases across the codebase, such as infinite wait loops on disconnected graphs.
* **Visuals & Rendering:** AI helped structure the `Pygame` visualization layer, including dynamic window resizing (`VIDEORESIZE`), smooth movement interpolation between turns.
* **Documentation**: Structuring and drafting the initial layout of this `README.md` file and writing docstrings.
