# D&D Maze Generator

A procedural dungeon maze generator for Dungeons & Dragons. Generates interconnected rooms with owners, treasures, and traps, linked by connection junctions on an expanded grid.

## Features

- **Grid-based architecture** — Rooms and connections are first-class nodes on an expanded grid
- **Room attributes** — Each room can have an owner/monster, treasure, and trap
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
  models.py      # MazeNode, Room, Connection, Maze, enums
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
