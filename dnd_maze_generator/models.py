"""Data models for the D&D Maze Generator."""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from typing import Optional


class Direction(enum.Enum):
    """Cardinal directions for room connections."""

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
class Connection:
    """A connection between two rooms in a specific direction.

    Attributes:
        direction: The cardinal direction of travel (N, E, S, W).
        destination: The room this connection leads to.
        length: The distance/time to traverse this connection (in arbitrary units).
    """

    direction: Direction
    destination: Room
    length: int

    def __str__(self) -> str:
        return (
            f"{self.direction.value} -> {self.destination.name} "
            f"(length: {self.length})"
        )


@dataclass
class Room:
    """A location in the maze/dungeon.

    Attributes:
        id: Unique identifier for the room.
        name: Descriptive name of the room.
        row: Grid row position.
        col: Grid column position.
        owner: The creature or NPC inhabiting this room.
        treasure: The type of treasure found in this room.
        trap: The type of trap in this room.
        connections: Dict mapping Direction to Connection objects.
    """

    id: int
    name: str
    row: int
    col: int
    owner: OwnerType = OwnerType.NONE
    treasure: TreasureType = TreasureType.NONE
    trap: TrapType = TrapType.NONE
    connections: dict[Direction, Connection] = field(default_factory=dict)

    def add_connection(self, direction: Direction, destination: Room, length: int) -> None:
        """Add a connection from this room to another room."""
        self.connections[direction] = Connection(
            direction=direction,
            destination=destination,
            length=length,
        )

    @property
    def connection_count(self) -> int:
        """Return the number of connections this room has."""
        return len(self.connections)

    def get_connection(self, direction: Direction) -> Optional[Connection]:
        """Get the connection in a given direction, or None if not connected."""
        return self.connections.get(direction)

    def has_connection(self, direction: Direction) -> bool:
        """Check if this room has a connection in the given direction."""
        return direction in self.connections

    def __str__(self) -> str:
        directions = ", ".join(d.value for d in self.connections)
        return (
            f"[{self.id}] {self.name} "
            f"(Owner: {self.owner.value}, "
            f"Treasure: {self.treasure.value}, "
            f"Trap: {self.trap.value}, "
            f"Exits: {directions})"
        )

    def __hash__(self) -> int:
        return hash(self.id)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Room):
            return NotImplemented
        return self.id == other.id


@dataclass
class Maze:
    """The complete dungeon maze.

    Attributes:
        width: Number of columns in the maze grid.
        height: Number of rows in the maze grid.
        rooms: 2D list of rooms indexed by [row][col].
        name: Name of this dungeon.
    """

    width: int
    height: int
    rooms: list[list[Room]] = field(default_factory=list)
    name: str = "The Dungeon"

    @property
    def all_rooms(self) -> list[Room]:
        """Return a flat list of all rooms in the maze."""
        return [room for row in self.rooms for room in row]

    @property
    def total_rooms(self) -> int:
        """Return the total number of rooms."""
        return self.width * self.height

    def get_room(self, row: int, col: int) -> Optional[Room]:
        """Get a room by its grid coordinates."""
        if 0 <= row < self.height and 0 <= col < self.width:
            return self.rooms[row][col]
        return None

    def __str__(self) -> str:
        return f"Maze '{self.name}' ({self.width}x{self.height}, {self.total_rooms} rooms)"
