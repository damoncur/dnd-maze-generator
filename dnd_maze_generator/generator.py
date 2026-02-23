"""Maze generation algorithm for the D&D Maze Generator."""

from __future__ import annotations

import random
from typing import Optional

from .models import (
    Direction,
    Maze,
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
    "Chamber", "Corridor", "Crypt", "Hall", "Cavern", "Den",
    "Dungeon", "Gallery", "Grotto", "Lair", "Passage", "Pit",
    "Sanctum", "Shrine", "Tomb", "Tunnel", "Vault", "Alcove",
    "Barracks", "Cell", "Chapel", "Forge", "Library", "Throne Room",
]

# Direction offsets: (row_delta, col_delta)
DIRECTION_DELTAS: dict[Direction, tuple[int, int]] = {
    Direction.NORTH: (-1, 0),
    Direction.SOUTH: (1, 0),
    Direction.EAST: (0, 1),
    Direction.WEST: (0, -1),
}


def _generate_room_name(used_names: set[str]) -> str:
    """Generate a unique room name."""
    for _ in range(100):
        adj = random.choice(ROOM_ADJECTIVES)
        noun = random.choice(ROOM_NOUNS)
        name = f"The {adj} {noun}"
        if name not in used_names:
            used_names.add(name)
            return name
    # Fallback with number suffix
    base = f"The {random.choice(ROOM_ADJECTIVES)} {random.choice(ROOM_NOUNS)}"
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

    Args:
        width: Number of columns in the maze grid.
        height: Number of rows in the maze grid.
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

    # Step 1: Create the grid of rooms
    rooms: list[list[Room]] = []
    room_id = 0
    for row in range(height):
        room_row: list[Room] = []
        for col in range(width):
            name = _generate_room_name(used_names)
            room = Room(
                id=room_id,
                name=name,
                row=row,
                col=col,
                owner=_random_owner(rng, owner_chance),
                treasure=_random_treasure(rng, treasure_chance),
                trap=_random_trap(rng, trap_chance),
            )
            room_row.append(room)
            room_id += 1
        rooms.append(room_row)

    # Step 2: Generate maze paths using randomized DFS (recursive backtracker)
    visited: set[tuple[int, int]] = set()
    stack: list[tuple[int, int]] = []

    # Start from a random cell
    start_row = rng.randint(0, height - 1)
    start_col = rng.randint(0, width - 1)
    visited.add((start_row, start_col))
    stack.append((start_row, start_col))

    while stack:
        current_row, current_col = stack[-1]
        current_room = rooms[current_row][current_col]

        # Find unvisited neighbors
        neighbors: list[tuple[Direction, int, int]] = []
        for direction, (dr, dc) in DIRECTION_DELTAS.items():
            nr, nc = current_row + dr, current_col + dc
            if 0 <= nr < height and 0 <= nc < width and (nr, nc) not in visited:
                neighbors.append((direction, nr, nc))

        if neighbors:
            # Choose a random unvisited neighbor
            direction, nr, nc = rng.choice(neighbors)
            neighbor_room = rooms[nr][nc]

            # Create bidirectional connection
            length = rng.randint(min_connection_length, max_connection_length)
            current_room.add_connection(direction, neighbor_room, length)
            neighbor_room.add_connection(direction.opposite, current_room, length)

            visited.add((nr, nc))
            stack.append((nr, nc))
        else:
            stack.pop()

    # Step 3: Optionally add extra connections to create loops
    for row in range(height):
        for col in range(width):
            current_room = rooms[row][col]
            for direction, (dr, dc) in DIRECTION_DELTAS.items():
                nr, nc = row + dr, col + dc
                if (
                    0 <= nr < height
                    and 0 <= nc < width
                    and not current_room.has_connection(direction)
                    and rng.random() < extra_connections
                ):
                    neighbor_room = rooms[nr][nc]
                    if not neighbor_room.has_connection(direction.opposite):
                        length = rng.randint(
                            min_connection_length, max_connection_length
                        )
                        current_room.add_connection(direction, neighbor_room, length)
                        neighbor_room.add_connection(
                            direction.opposite, current_room, length
                        )

    maze = Maze(
        width=width,
        height=height,
        rooms=rooms,
        name=dungeon_name,
    )

    return maze
