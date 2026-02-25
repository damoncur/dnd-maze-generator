"""Data models for the D&D Maze Generator.

The maze lives on an expanded grid where:
- Rooms sit at even-row, even-col positions.
- Connections sit at mixed-parity positions (between rooms).
- Odd-row, odd-col positions are always opaque walls.

Each cell, when rendered, is a 3x3 tile:
    [corner] [N exit] [corner]
    [W exit] [center] [E exit]
    [corner] [S exit] [corner]

Corners (positions 1, 3, 7, 9) are always opaque because movement
is restricted to cardinal directions only.
"""

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


class CellType(enum.Enum):
    """Types of cells on the expanded maze grid."""

    ROOM = "Room"
    CONNECTION = "Connection"
    WALL = "Wall"


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
    """Base class for all traversable points in the maze.

    Both rooms and connections live on the expanded grid.  Each node
    tracks its grid position (row, col) and connections to neighbors
    via the four cardinal directions.

    Attributes:
        id: Unique identifier for this node.
        name: Descriptive name of this node.
        row: Row position on the expanded grid.
        col: Column position on the expanded grid.
        connections: Dict mapping Direction to neighboring MazeNode.
    """

    id: int
    name: str
    row: int = 0
    col: int = 0
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
        return f"[{self.id}] {self.name} ({self.row},{self.col}) (Exits: {directions})"


@dataclass(eq=False)
class Connection(MazeNode):
    """A connection/junction node on the maze grid.

    Connections sit between rooms on the expanded grid.  A connection
    can be 1-way (dead end), 2-way (passage), 3-way (T-junction),
    or 4-way (crossroads), depending on how many exits it has.

    Attributes:
        length: The distance/time to traverse this connection.
    """

    length: int = 1

    @property
    def ways(self) -> int:
        """Number of directions this connection opens to (1-4)."""
        return self.connection_count

    def __str__(self) -> str:
        directions = ", ".join(d.value for d in self.connections)
        return (
            f"[{self.id}] {self.name} ({self.row},{self.col}) "
            f"({self.ways}-way, length: {self.length}, Exits: {directions})"
        )


@dataclass(eq=False)
class Room(MazeNode):
    """A room/location node in the maze.

    Rooms sit at even-row, even-col positions on the expanded grid.
    They can contain creatures, treasure, and traps.

    Attributes:
        owner: The creature or NPC inhabiting this room.
        treasure: The type of treasure found in this room.
        trap: The type of trap in this room.
    """

    owner: OwnerType = OwnerType.NONE
    treasure: TreasureType = TreasureType.NONE
    trap: TrapType = TrapType.NONE

    def __str__(self) -> str:
        directions = ", ".join(d.value for d in self.connections)
        return (
            f"[{self.id}] {self.name} ({self.row},{self.col}) "
            f"(Owner: {self.owner.value}, "
            f"Treasure: {self.treasure.value}, "
            f"Trap: {self.trap.value}, "
            f"Exits: {directions})"
        )


@dataclass
class Maze:
    """The complete dungeon maze on an expanded grid.

    The grid is structured as:
    - Even row, even col -> Room
    - One even / one odd  -> Connection (between adjacent rooms)
    - Odd row, odd col    -> Wall (opaque corner, always None)

    Attributes:
        rooms_wide: Number of room columns (logical width).
        rooms_tall: Number of room rows (logical height).
        grid: 2-D list of nodes; None means wall / empty.
        entry: The starting Connection node (maze entrance).
        name: Name of this dungeon.
    """

    rooms_wide: int
    rooms_tall: int
    grid: list[list[Optional[MazeNode]]] = field(default_factory=list)
    entry: Optional[Connection] = None
    name: str = "The Dungeon"

    @property
    def grid_width(self) -> int:
        """Width of the expanded grid."""
        if self.rooms_wide <= 0:
            return 0
        return 2 * self.rooms_wide - 1

    @property
    def grid_height(self) -> int:
        """Height of the expanded grid."""
        if self.rooms_tall <= 0:
            return 0
        return 2 * self.rooms_tall - 1

    def get_cell(self, row: int, col: int) -> Optional[MazeNode]:
        """Get the node at an expanded-grid position, or None."""
        if 0 <= row < len(self.grid) and self.grid and 0 <= col < len(self.grid[0]):
            return self.grid[row][col]
        return None

    @staticmethod
    def cell_type_at(row: int, col: int) -> CellType:
        """Determine the expected cell type from grid coordinates."""
        if row % 2 == 0 and col % 2 == 0:
            return CellType.ROOM
        if row % 2 == 1 and col % 2 == 1:
            return CellType.WALL
        return CellType.CONNECTION

    def get_room(self, logical_row: int, logical_col: int) -> Optional[Room]:
        """Get a room by its logical position (not expanded-grid position)."""
        grid_row = logical_row * 2
        grid_col = logical_col * 2
        cell = self.get_cell(grid_row, grid_col)
        if isinstance(cell, Room):
            return cell
        return None

    @property
    def all_rooms(self) -> list[Room]:
        """Return a flat list of all rooms in the maze."""
        return [
            cell
            for row in self.grid
            for cell in row
            if isinstance(cell, Room)
        ]

    @property
    def all_connections(self) -> list[Connection]:
        """Return a flat list of all connection nodes in the maze."""
        return [
            cell
            for row in self.grid
            for cell in row
            if isinstance(cell, Connection)
        ]

    @property
    def all_nodes(self) -> list[MazeNode]:
        """Return a flat list of all nodes (rooms + connections)."""
        return [
            cell
            for row in self.grid
            for cell in row
            if cell is not None
        ]

    @property
    def total_rooms(self) -> int:
        """Return the expected number of rooms (logical width * height)."""
        return self.rooms_wide * self.rooms_tall

    @property
    def total_nodes(self) -> int:
        """Return the total number of active nodes on the grid."""
        return len(self.all_nodes)

    def __str__(self) -> str:
        return (
            f"Maze '{self.name}' ({self.rooms_wide}x{self.rooms_tall} rooms, "
            f"{len(self.all_connections)} connections)"
        )
