# D&D Maze Generator

A procedural dungeon maze generator for Dungeons & Dragons. Generates interconnected rooms with owners, treasures, and traps, linked by connection junctions on an expanded grid.

## Features

- **Grid-based architecture** — Rooms and connections are first-class nodes on an expanded grid
- **Room attributes** — Each room can have an owner/monster, treasure, and trap
- **Doors** — Room exits can have doors with type, lock, trap, and open/closed state
- **Connection junctions** — 1-way (dead end), 2-way (passage), 3-way (T-junction), or 4-way (crossroads)
- **3x3 tile ASCII rendering** — Visual map with opaque corners and directional exits
- **Randomized DFS** maze generation with optional extra connections for loops
- **Reproducible** mazes via seed parameter
- **CLI interface** with full customization

## Installation

```bash
pip install -e .
```

## Quick Start

```bash
# Generate a default 5x5 maze
python -m dnd_maze_generator

# Generate a 3x3 maze with a fixed seed
python -m dnd_maze_generator -W 3 -H 3 -s 42

# Name your dungeon
python -m dnd_maze_generator -W 4 -H 4 -s 100 -n "Dragon's Lair"
```

## CLI Options

```
python -m dnd_maze_generator --help

Options:
  -W, --width WIDTH              Number of room columns (default: 5)
  -H, --height HEIGHT            Number of room rows (default: 5)
  -s, --seed SEED                Random seed for reproducible mazes
  --min-length MIN_LENGTH        Minimum connection traversal length (default: 1)
  --max-length MAX_LENGTH        Maximum connection traversal length (default: 10)
  --owner-chance OWNER_CHANCE    Probability (0-1) a room has a monster (default: 0.4)
  --treasure-chance TREASURE_CHANCE  Probability (0-1) a room has treasure (default: 0.3)
  --trap-chance TRAP_CHANCE      Probability (0-1) a room has a trap (default: 0.25)
  --extra-connections EXTRA_CONNECTIONS  Probability (0-1) of loop connections (default: 0.1)
  --door-chance DOOR_CHANCE      Probability (0-1) a room exit has a door (default: 0.5)
  --lock-chance LOCK_CHANCE      Probability (0-1) a door has a lock (default: 0.3)
  --door-trap-chance DOOR_TRAP_CHANCE  Probability (0-1) a door has a trap (default: 0.2)
  -n, --name NAME                Dungeon name (default: "The Dungeon")
```

## Example Output

```
$ python -m dnd_maze_generator -W 3 -H 3 -s 42

Grid: 5x5 (3x3 rooms)
Entry: [15] The Ancient Bridge

--- MAP ---
###############
#0  *  1  +  2#
############# #
############# #
#############+#
############# #
############# #
#3#####4  +  5#
# ##### ##### #
# ##### ##### #
#+#####+#####+#
# ##### ##### #
# ##### ##### #
#6  +  7#####8#
###############
```

**Map legend:**
- `0`-`9`, `A`-`Z`, `a`-`z` — Room IDs
- `+` — Connection junction
- `*` — Maze entry point
- `#` — Wall
- ` ` (space) — Open passage

## Doors

Doors can appear at room exits. Each door has:

| Attribute | Values |
|---|---|
| **Type** | Large Rock, Wooden, Iron, Steel, Hidden |
| **Lock** | None, Key Lock, Combination Lock, Magic Lock, Barred, Padlock |
| **Trap** | None, Poison Needle, Acid Spray, Alarm, Blade, Shock |
| **State** | Open or Closed |

Each door also references the **room** it belongs to and the **corridor** (connection) it leads to.

Doors are generated randomly per room exit. A corridor between two rooms can have 0, 1, or 2 doors (one on each side). Use `--door-chance 0.0` to disable doors entirely, or `--door-chance 1.0` to guarantee a door at every exit.

```bash
# Full doors with locks and traps
python -m dnd_maze_generator -W 3 -H 3 -s 42 --door-chance 1.0 --lock-chance 0.5 --door-trap-chance 0.5

# No doors
python -m dnd_maze_generator -W 3 -H 3 -s 42 --door-chance 0.0
```

## Grid Model

The maze uses an expanded grid where:

| Grid Position | Cell Type | Description |
|---|---|---|
| Even row, even col | **Room** | Rooms with owner, treasure, trap |
| Mixed parity | **Connection** | Junctions between rooms (1-4 way) |
| Odd row, odd col | **Wall** | Always opaque/impassable |

Each cell renders as a 3x3 tile with opaque corners — movement is cardinal directions only (N/E/S/W).

## Running Tests

```bash
pip install pytest
python -m pytest tests/ -v
```

## Project Structure

```
dnd_maze_generator/
  models.py      # MazeNode, Room, Connection, Door, Maze, enums
  generator.py   # Randomized DFS maze generation
  display.py     # 3x3 tile ASCII rendering
  cli.py         # Command-line interface
tests/
  test_models.py
  test_generator.py
  test_display.py
  test_cli.py
```

## License

MIT
