"""Maze generation algorithm for the D&D Maze Generator."""

from __future__ import annotations

import random
from typing import Optional

from .models import (
    Corridor,
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
    "Chamber", "Crypt", "Hall", "Cavern", "Den",
    "Dungeon", "Gallery", "Grotto", "Lair", "Pit",
    "Sanctum", "Shrine", "Tomb", "Vault", "Alcove",
    "Barracks", "Cell", "Chapel", "Forge", "Library", "Throne Room",
]

CORRIDOR_ADJECTIVES = [
    "Dark", "Narrow", "Winding", "Crumbling", "Damp", "Shadowy",
    "Long", "Twisted", "Mossy", "Dusty", "Cold", "Echoing",
    "Dim", "Steep", "Hidden", "Ancient", "Worn", "Slippery",
]

CORRIDOR_NOUNS = [
    "Corridor", "Passage", "Tunnel", "Hallway", "Walkway",
    "Path", "Bridge", "Stairway", "Crawlway", "Alley",
]

# Direction offsets: (row_delta, col_delta)
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


def _generate_corridor_name(rng: random.Random, used_names: set[str]) -> str:
    """Generate a unique corridor name."""
    for _ in range(100):
        adj = rng.choice(CORRIDOR_ADJECTIVES)
        noun = rng.choice(CORRIDOR_NOUNS)
        name = f"The {adj} {noun}"
        if name not in used_names:
            used_names.add(name)
            return name
    base = f"The {rng.choice(CORRIDOR_ADJECTIVES)} {rng.choice(CORRIDOR_NOUNS)}"
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


def _create_corridor_between(
    room_a: Room,
    room_b: Room,
    direction: Direction,
    length: int,
    corridor_id: int,
    corridor_name: str,
) -> Corridor:
    """Create a corridor node between two rooms and wire up all connections.

    The corridor sits between room_a and room_b along the given direction:
        room_a --(direction)--> corridor --(direction)--> room_b
        room_b --(opposite)--> corridor --(opposite)--> room_a

    Args:
        room_a: The source room.
        room_b: The destination room.
        direction: The direction from room_a to room_b.
        length: The traversal length of this corridor.
        corridor_id: Unique ID for the new corridor.
        corridor_name: Name for the new corridor.

    Returns:
        The newly created Corridor node.
    """
    corridor = Corridor(
        id=corridor_id,
        name=corridor_name,
        length=length,
    )
    # room_a <-> corridor in the forward direction
    room_a.add_connection(direction, corridor)
    corridor.add_connection(direction.opposite, room_a)
    # corridor <-> room_b in the forward direction
    corridor.add_connection(direction, room_b)
    room_b.add_connection(direction.opposite, corridor)
    return corridor


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

    Each pair of connected rooms has a Corridor node between them.
    Corridors are first-class nodes that can themselves have connections,
    making every point in the maze (room or corridor) a node in the graph.

    Args:
        width: Number of columns in the maze grid.
        height: Number of rows in the maze grid.
        seed: Random seed for reproducibility. None for random.
        min_connection_length: Minimum traversal length for corridors.
        max_connection_length: Maximum traversal length for corridors.
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
    corridors: list[Corridor] = []
    next_id = 0

    # Step 1: Create the grid of rooms
    rooms: list[list[Room]] = []
    for row in range(height):
        room_row: list[Room] = []
        for col in range(width):
            name = _generate_room_name(rng, used_names)
            room = Room(
                id=next_id,
                name=name,
                row=row,
                col=col,
                owner=_random_owner(rng, owner_chance),
                treasure=_random_treasure(rng, treasure_chance),
                trap=_random_trap(rng, trap_chance),
            )
            room_row.append(room)
            next_id += 1
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

            # Create a corridor node between the two rooms
            length = rng.randint(min_connection_length, max_connection_length)
            corridor_name = _generate_corridor_name(rng, used_names)
            corridor = _create_corridor_between(
                current_room, neighbor_room, direction, length,
                corridor_id=next_id, corridor_name=corridor_name,
            )
            corridors.append(corridor)
            next_id += 1

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
                        corridor_name = _generate_corridor_name(rng, used_names)
                        corridor = _create_corridor_between(
                            current_room, neighbor_room, direction, length,
                            corridor_id=next_id, corridor_name=corridor_name,
                        )
                        corridors.append(corridor)
                        next_id += 1

    maze = Maze(
        width=width,
        height=height,
        rooms=rooms,
        corridors=corridors,
        name=dungeon_name,
    )

    return maze
