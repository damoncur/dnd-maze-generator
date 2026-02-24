"""Data models for the D&D Maze Generator."""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from typing import Optional


class Direction(enum.Enum):
    """Cardinal directions for node connections."""

    NORTH = "N"
    EAST = "E"
    SOUTH = "S"
    WEST = "W"

    @property
    def opposite(self) -> Direction:
        """Return the opposite direction."""
        opposites = {
            Direction.NORTH: Direction.SOUTH,
            Direction.SOUTH: Direction.NORTH,
            Direction.EAST: Direction.WEST,
            Direction.WEST: Direction.EAST,
        }
        return opposites[self]

    def __str__(self) -> str:
        return self.value


class TrapType(enum.Enum):
    """Types of traps that can be found in a room."""

    NONE = "None"
    PIT = "Pit Trap"
    POISON_DART = "Poison Dart Trap"
    SPIKE = "Spike Trap"
    FIRE = "Fire Trap"
    ROLLING_BOULDER = "Rolling Boulder"
    COLLAPSING_CEILING = "Collapsing Ceiling"
    POISON_GAS = "Poison Gas"
    ARROW = "Arrow Trap"


class TreasureType(enum.Enum):
    """Types of treasure that can be found in a room."""

    NONE = "None"
    GOLD_COINS = "Gold Coins"
    SILVER_COINS = "Silver Coins"
    GEMS = "Gems"
    MAGIC_WEAPON = "Magic Weapon"
    MAGIC_ARMOR = "Magic Armor"
    POTION = "Potion"
    SCROLL = "Scroll"
    RING = "Magic Ring"
    CHEST = "Treasure Chest"


class OwnerType(enum.Enum):
    """Types of owners/inhabitants of a room."""

    NONE = "Empty"
    GOBLIN = "Goblin"
    ORC = "Orc"
    SKELETON = "Skeleton"
    ZOMBIE = "Zombie"
    SPIDER = "Giant Spider"
    RAT = "Giant Rat"
    DRAGON = "Dragon"
    MIMIC = "Mimic"
    LICH = "Lich"
    BANDIT = "Bandit"
    GHOST = "Ghost"


@dataclass
class MazeNode:
    """Base class for all points in the maze (rooms and corridors).

    Both rooms and corridors are first-class nodes in the maze graph.
    Each node can connect to up to four other nodes via the cardinal
    directions (N, E, S, W).

    Attributes:
        id: Unique identifier for this node.
        name: Descriptive name of this node.
        connections: Dict mapping Direction to neighboring MazeNode objects.
    """

    id: int
    name: str
    connections: dict[Direction, MazeNode] = field(default_factory=dict)

    def add_connection(self, direction: Direction, destination: MazeNode) -> None:
        """Add a connection from this node to another node in the given direction."""
        self.connections[direction] = destination

    @property
    def connection_count(self) -> int:
        """Return the number of connections this node has."""
        return len(self.connections)

    def get_connection(self, direction: Direction) -> Optional[MazeNode]:
        """Get the neighboring node in a given direction, or None."""
        return self.connections.get(direction)

    def has_connection(self, direction: Direction) -> bool:
        """Check if this node has a connection in the given direction."""
        return direction in self.connections

    def __hash__(self) -> int:
        return hash(self.id)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, MazeNode):
            return NotImplemented
        return self.id == other.id

    def __str__(self) -> str:
        directions = ", ".join(d.value for d in self.connections)
        return f"[{self.id}] {self.name} (Exits: {directions})"


@dataclass(eq=False)
class Corridor(MazeNode):
    """A corridor/passage node in the maze.

    Corridors are first-class nodes that sit between rooms (or other corridors).
    They represent hallways, tunnels, passages, etc. A corridor can branch off
    to connect to additional nodes in any cardinal direction, just like a room.

    Attributes:
        length: The distance/time to traverse this corridor (in arbitrary units).
    """

    length: int = 1

    def __str__(self) -> str:
        directions = ", ".join(d.value for d in self.connections)
        return f"[{self.id}] {self.name} (length: {self.length}, Exits: {directions})"


@dataclass(eq=False)
class Room(MazeNode):
    """A room/location node in the maze.

    Rooms are points in the maze that can contain creatures, treasure, and traps.
    They connect to corridors (or directly to other rooms) via cardinal directions.

    Attributes:
        row: Grid row position.
        col: Grid column position.
        owner: The creature or NPC inhabiting this room.
        treasure: The type of treasure found in this room.
        trap: The type of trap in this room.
    """

    row: int = 0
    col: int = 0
    owner: OwnerType = OwnerType.NONE
    treasure: TreasureType = TreasureType.NONE
    trap: TrapType = TrapType.NONE

    def __str__(self) -> str:
        directions = ", ".join(d.value for d in self.connections)
        return (
            f"[{self.id}] {self.name} "
            f"(Owner: {self.owner.value}, "
            f"Treasure: {self.treasure.value}, "
            f"Trap: {self.trap.value}, "
            f"Exits: {directions})"
        )


@dataclass
class Maze:
    """The complete dungeon maze.

    The maze is a graph of interconnected MazeNodes (rooms and corridors).
    Rooms sit on a grid, and corridors sit between them as intermediary nodes.
    Both rooms and corridors are points that can connect to other points.

    Attributes:
        width: Number of columns in the room grid.
        height: Number of rows in the room grid.
        rooms: 2D list of rooms indexed by [row][col].
        corridors: List of all corridor nodes in the maze.
        name: Name of this dungeon.
    """

    width: int
    height: int
    rooms: list[list[Room]] = field(default_factory=list)
    corridors: list[Corridor] = field(default_factory=list)
    name: str = "The Dungeon"

    @property
    def all_rooms(self) -> list[Room]:
        """Return a flat list of all rooms in the maze."""
        return [room for row in self.rooms for room in row]

    @property
    def all_nodes(self) -> list[MazeNode]:
        """Return a flat list of all nodes (rooms + corridors) in the maze."""
        nodes: list[MazeNode] = list(self.all_rooms)
        nodes.extend(self.corridors)
        return nodes

    @property
    def total_rooms(self) -> int:
        """Return the total number of rooms."""
        return self.width * self.height

    @property
    def total_nodes(self) -> int:
        """Return the total number of nodes (rooms + corridors)."""
        return self.total_rooms + len(self.corridors)

    def get_room(self, row: int, col: int) -> Optional[Room]:
        """Get a room by its grid coordinates."""
        if 0 <= row < self.height and 0 <= col < self.width:
            return self.rooms[row][col]
        return None

    def __str__(self) -> str:
        return (
            f"Maze '{self.name}' ({self.width}x{self.height}, "
            f"{self.total_rooms} rooms, {len(self.corridors)} corridors)"
        )
