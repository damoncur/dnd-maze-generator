"""Maze generation algorithm for the D&D Maze Generator.

The generator builds an expanded grid where rooms sit at even-row,
even-col positions and connection nodes sit at the mixed-parity
positions between them.  Odd-odd positions are opaque walls.

The maze is carved with randomized DFS (recursive backtracker),
then optional extra connections are added for loops.  Finally a
boundary connection is chosen as the maze entry point.
"""

from __future__ import annotations

import random
from typing import Optional

from .models import (
    Connection,
    Direction,
    Maze,
    MazeNode,
    OwnerType,
    Room,
    TrapType,
    TreasureType,
)

# Room name components for procedural generation
ROOM_ADJECTIVES = [
    "Dark", "Dusty", "Crumbling", "Damp", "Eerie", "Forgotten",
    "Gloomy", "Haunted", "Icy", "Jagged", "Looming", "Mossy",
    "Narrow", "Overgrown", "Putrid", "Quiet", "Ruined", "Shadowy",
    "Twisted", "Unholy", "Vast", "Winding", "Ancient", "Burning",
]

ROOM_NOUNS = [
    "Chamber", "Crypt", "Hall", "Cavern", "Den",
    "Dungeon", "Gallery", "Grotto", "Lair", "Pit",
    "Sanctum", "Shrine", "Tomb", "Vault", "Alcove",
    "Barracks", "Cell", "Chapel", "Forge", "Library", "Throne Room",
]

CONNECTION_ADJECTIVES = [
    "Dark", "Narrow", "Winding", "Crumbling", "Damp", "Shadowy",
    "Long", "Twisted", "Mossy", "Dusty", "Cold", "Echoing",
    "Dim", "Steep", "Hidden", "Ancient", "Worn", "Slippery",
]

CONNECTION_NOUNS = [
    "Corridor", "Passage", "Tunnel", "Hallway", "Walkway",
    "Path", "Bridge", "Stairway", "Crawlway", "Alley",
]

# Direction offsets on the *logical* room grid: (row_delta, col_delta)
DIRECTION_DELTAS: dict[Direction, tuple[int, int]] = {
    Direction.NORTH: (-1, 0),
    Direction.SOUTH: (1, 0),
    Direction.EAST: (0, 1),
    Direction.WEST: (0, -1),
}


def _generate_room_name(rng: random.Random, used_names: set[str]) -> str:
    """Generate a unique room name."""
    for _ in range(100):
        adj = rng.choice(ROOM_ADJECTIVES)
        noun = rng.choice(ROOM_NOUNS)
        name = f"The {adj} {noun}"
        if name not in used_names:
            used_names.add(name)
            return name
    # Fallback with number suffix
    base = f"The {rng.choice(ROOM_ADJECTIVES)} {rng.choice(ROOM_NOUNS)}"
    counter = 2
    while f"{base} {counter}" in used_names:
        counter += 1
    name = f"{base} {counter}"
    used_names.add(name)
    return name


def _generate_connection_name(rng: random.Random, used_names: set[str]) -> str:
    """Generate a unique connection name."""
    for _ in range(100):
        adj = rng.choice(CONNECTION_ADJECTIVES)
        noun = rng.choice(CONNECTION_NOUNS)
        name = f"The {adj} {noun}"
        if name not in used_names:
            used_names.add(name)
            return name
    base = f"The {rng.choice(CONNECTION_ADJECTIVES)} {rng.choice(CONNECTION_NOUNS)}"
    counter = 2
    while f"{base} {counter}" in used_names:
        counter += 1
    name = f"{base} {counter}"
    used_names.add(name)
    return name


def _random_owner(
    rng: random.Random,
    owner_chance: float = 0.4,
) -> OwnerType:
    """Randomly assign an owner to a room."""
    if rng.random() > owner_chance:
        return OwnerType.NONE
    owners = [o for o in OwnerType if o != OwnerType.NONE]
    return rng.choice(owners)


def _random_treasure(
    rng: random.Random,
    treasure_chance: float = 0.3,
) -> TreasureType:
    """Randomly assign treasure to a room."""
    if rng.random() > treasure_chance:
        return TreasureType.NONE
    treasures = [t for t in TreasureType if t != TreasureType.NONE]
    return rng.choice(treasures)


def _random_trap(
    rng: random.Random,
    trap_chance: float = 0.25,
) -> TrapType:
    """Randomly assign a trap to a room."""
    if rng.random() > trap_chance:
        return TrapType.NONE
    traps = [t for t in TrapType if t != TrapType.NONE]
    return rng.choice(traps)


def _create_connection_between(
    room_a: Room,
    room_b: Room,
    direction: Direction,
    length: int,
    conn_id: int,
    conn_name: str,
    grid_row: int,
    grid_col: int,
) -> Connection:
    """Create a connection node between two rooms and wire up all links.

    The connection sits on the expanded grid between room_a and room_b:
        room_a --(direction)--> connection --(direction)--> room_b
        room_b --(opposite)--> connection --(opposite)--> room_a

    Args:
        room_a: The source room.
        room_b: The destination room.
        direction: The direction from room_a to room_b.
        length: The traversal length of this connection.
        conn_id: Unique ID for the new connection.
        conn_name: Name for the new connection.
        grid_row: Row on the expanded grid where this connection sits.
        grid_col: Column on the expanded grid where this connection sits.

    Returns:
        The newly created Connection node.
    """
    connection = Connection(
        id=conn_id,
        name=conn_name,
        row=grid_row,
        col=grid_col,
        length=length,
    )
    # room_a <-> connection in the forward direction
    room_a.add_connection(direction, connection)
    connection.add_connection(direction.opposite, room_a)
    # connection <-> room_b in the forward direction
    connection.add_connection(direction, room_b)
    room_b.add_connection(direction.opposite, connection)
    return connection


def generate_maze(
    width: int = 5,
    height: int = 5,
    seed: Optional[int] = None,
    min_connection_length: int = 1,
    max_connection_length: int = 10,
    owner_chance: float = 0.4,
    treasure_chance: float = 0.3,
    trap_chance: float = 0.25,
    extra_connections: float = 0.1,
    dungeon_name: str = "The Dungeon",
) -> Maze:
    """Generate a maze using randomized DFS (recursive backtracker).

    The maze is built on an expanded grid where rooms sit at even
    positions and connection nodes sit between them.  The maze starts
    at a connection (the entry point).

    Args:
        width: Number of room columns (logical width).
        height: Number of room rows (logical height).
        seed: Random seed for reproducibility. None for random.
        min_connection_length: Minimum traversal length for connections.
        max_connection_length: Maximum traversal length for connections.
        owner_chance: Probability (0-1) that a room has an owner.
        treasure_chance: Probability (0-1) that a room has treasure.
        trap_chance: Probability (0-1) that a room has a trap.
        extra_connections: Probability (0-1) of adding extra connections
            beyond the spanning tree to create loops.
        dungeon_name: Name for the dungeon.

    Returns:
        A fully generated Maze object.
    """
    rng = random.Random(seed)
    used_names: set[str] = set()
    next_id = 0

    # Compute expanded grid dimensions
    grid_h = max(2 * height - 1, 0) if height > 0 else 0
    grid_w = max(2 * width - 1, 0) if width > 0 else 0

    # Initialise grid with None (walls / empty)
    grid: list[list[Optional[MazeNode]]] = [
        [None] * grid_w for _ in range(grid_h)
    ]

    # Step 1: Place rooms at even-row, even-col positions
    for r in range(height):
        for c in range(width):
            gr, gc = r * 2, c * 2
            name = _generate_room_name(rng, used_names)
            room = Room(
                id=next_id,
                name=name,
                row=gr,
                col=gc,
                owner=_random_owner(rng, owner_chance),
                treasure=_random_treasure(rng, treasure_chance),
                trap=_random_trap(rng, trap_chance),
            )
            grid[gr][gc] = room
            next_id += 1

    # Step 2: Randomized DFS to carve connections between rooms
    visited: set[tuple[int, int]] = set()
    stack: list[tuple[int, int]] = []

    start_row = rng.randint(0, height - 1)
    start_col = rng.randint(0, width - 1)
    visited.add((start_row, start_col))
    stack.append((start_row, start_col))

    while stack:
        cr, cc = stack[-1]

        # Find unvisited room neighbours
        neighbors: list[tuple[Direction, int, int]] = []
        for direction, (dr, dc) in DIRECTION_DELTAS.items():
            nr, nc = cr + dr, cc + dc
            if 0 <= nr < height and 0 <= nc < width and (nr, nc) not in visited:
                neighbors.append((direction, nr, nc))

        if neighbors:
            direction, nr, nc = rng.choice(neighbors)

            # Grid positions
            cur_gr, cur_gc = cr * 2, cc * 2
            nbr_gr, nbr_gc = nr * 2, nc * 2
            conn_gr = (cur_gr + nbr_gr) // 2
            conn_gc = (cur_gc + nbr_gc) // 2

            current_room = grid[cur_gr][cur_gc]
            neighbor_room = grid[nbr_gr][nbr_gc]

            length = rng.randint(min_connection_length, max_connection_length)
            conn_name = _generate_connection_name(rng, used_names)

            assert isinstance(current_room, Room)
            assert isinstance(neighbor_room, Room)
            connection = _create_connection_between(
                current_room, neighbor_room, direction, length,
                conn_id=next_id, conn_name=conn_name,
                grid_row=conn_gr, grid_col=conn_gc,
            )
            grid[conn_gr][conn_gc] = connection
            next_id += 1

            visited.add((nr, nc))
            stack.append((nr, nc))
        else:
            stack.pop()

    # Step 3: Optionally add extra connections to create loops
    for r in range(height):
        for c in range(width):
            cur_gr, cur_gc = r * 2, c * 2
            current_room = grid[cur_gr][cur_gc]
            assert isinstance(current_room, Room)

            for direction, (dr, dc) in DIRECTION_DELTAS.items():
                nr, nc = r + dr, c + dc
                if (
                    0 <= nr < height
                    and 0 <= nc < width
                    and not current_room.has_connection(direction)
                    and rng.random() < extra_connections
                ):
                    nbr_gr, nbr_gc = nr * 2, nc * 2
                    neighbor_room = grid[nbr_gr][nbr_gc]
                    assert isinstance(neighbor_room, Room)

                    if not neighbor_room.has_connection(direction.opposite):
                        conn_gr = (cur_gr + nbr_gr) // 2
                        conn_gc = (cur_gc + nbr_gc) // 2

                        length = rng.randint(
                            min_connection_length, max_connection_length
                        )
                        conn_name = _generate_connection_name(rng, used_names)
                        connection = _create_connection_between(
                            current_room, neighbor_room, direction, length,
                            conn_id=next_id, conn_name=conn_name,
                            grid_row=conn_gr, grid_col=conn_gc,
                        )
                        grid[conn_gr][conn_gc] = connection
                        next_id += 1

    # Step 4: Choose an entry connection (prefer one on the grid boundary)
    entry: Optional[Connection] = None
    all_connections = [
        cell
        for row in grid
        for cell in row
        if isinstance(cell, Connection)
    ]
    for conn in all_connections:
        if (
            conn.row == 0
            or conn.row == grid_h - 1
            or conn.col == 0
            or conn.col == grid_w - 1
        ):
            entry = conn
            break
    if entry is None and all_connections:
        entry = all_connections[0]

    return Maze(
        rooms_wide=width,
        rooms_tall=height,
        grid=grid,
        entry=entry,
        name=dungeon_name,
    )
