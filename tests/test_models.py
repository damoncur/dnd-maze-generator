"""Tests for the data models."""

from dnd_maze_generator.models import (
    CellType,
    Connection,
    Direction,
    Maze,
    MazeNode,
    OwnerType,
    Room,
    TrapType,
    TreasureType,
)


class TestDirection:
    def test_opposite_north_south(self) -> None:
        assert Direction.NORTH.opposite == Direction.SOUTH
        assert Direction.SOUTH.opposite == Direction.NORTH

    def test_opposite_east_west(self) -> None:
        assert Direction.EAST.opposite == Direction.WEST
        assert Direction.WEST.opposite == Direction.EAST

    def test_str(self) -> None:
        assert str(Direction.NORTH) == "N"
        assert str(Direction.EAST) == "E"
        assert str(Direction.SOUTH) == "S"
        assert str(Direction.WEST) == "W"

    def test_values(self) -> None:
        assert Direction.NORTH.value == "N"
        assert Direction.EAST.value == "E"
        assert Direction.SOUTH.value == "S"
        assert Direction.WEST.value == "W"


class TestCellType:
    def test_room_at_even_even(self) -> None:
        assert Maze.cell_type_at(0, 0) == CellType.ROOM
        assert Maze.cell_type_at(2, 4) == CellType.ROOM

    def test_connection_at_mixed_parity(self) -> None:
        assert Maze.cell_type_at(0, 1) == CellType.CONNECTION
        assert Maze.cell_type_at(1, 0) == CellType.CONNECTION

    def test_wall_at_odd_odd(self) -> None:
        assert Maze.cell_type_at(1, 1) == CellType.WALL
        assert Maze.cell_type_at(3, 3) == CellType.WALL


class TestMazeNode:
    def test_add_connection(self) -> None:
        node_a = MazeNode(id=0, name="Node A")
        node_b = MazeNode(id=1, name="Node B")
        node_a.add_connection(Direction.NORTH, node_b)

        assert node_a.connection_count == 1
        assert node_a.has_connection(Direction.NORTH)
        assert not node_a.has_connection(Direction.SOUTH)

    def test_get_connection(self) -> None:
        node_a = MazeNode(id=0, name="Node A")
        node_b = MazeNode(id=1, name="Node B")
        node_a.add_connection(Direction.EAST, node_b)

        neighbor = node_a.get_connection(Direction.EAST)
        assert neighbor is not None
        assert neighbor == node_b
        assert node_a.get_connection(Direction.WEST) is None

    def test_has_row_col(self) -> None:
        node = MazeNode(id=0, name="Node", row=3, col=5)
        assert node.row == 3
        assert node.col == 5

    def test_equality(self) -> None:
        node_a = MazeNode(id=0, name="A")
        node_b = MazeNode(id=0, name="B")
        node_c = MazeNode(id=1, name="C")
        assert node_a == node_b  # Same ID
        assert node_a != node_c  # Different ID

    def test_hash(self) -> None:
        node_a = MazeNode(id=0, name="A")
        node_b = MazeNode(id=0, name="B")
        assert hash(node_a) == hash(node_b)

    def test_str(self) -> None:
        node = MazeNode(id=5, name="Test Node", row=2, col=4)
        s = str(node)
        assert "5" in s
        assert "Test Node" in s
        assert "(2,4)" in s

    def test_cross_type_equality(self) -> None:
        """Room and Connection with same ID should be equal (both are MazeNodes)."""
        room = Room(id=0, name="Room")
        conn = Connection(id=0, name="Connection", length=5)
        assert room == conn


class TestRoom:
    def _make_room(self, room_id: int = 0, name: str = "Test Room") -> Room:
        return Room(id=room_id, name=name, row=0, col=0)

    def test_default_attributes(self) -> None:
        room = self._make_room()
        assert room.owner == OwnerType.NONE
        assert room.treasure == TreasureType.NONE
        assert room.trap == TrapType.NONE
        assert room.connections == {}

    def test_connect_to_connection(self) -> None:
        room = self._make_room(0, "Room")
        conn = Connection(id=10, name="Passage", row=0, col=1, length=5)
        room.add_connection(Direction.EAST, conn)

        assert room.connection_count == 1
        neighbor = room.get_connection(Direction.EAST)
        assert neighbor is not None
        assert isinstance(neighbor, Connection)
        assert neighbor.length == 5

    def test_str(self) -> None:
        room = Room(
            id=1,
            name="Dark Chamber",
            row=0,
            col=0,
            owner=OwnerType.GOBLIN,
            treasure=TreasureType.GOLD_COINS,
            trap=TrapType.PIT,
        )
        s = str(room)
        assert "Dark Chamber" in s
        assert "Goblin" in s
        assert "Gold Coins" in s
        assert "Pit Trap" in s


class TestConnection:
    def test_default_length(self) -> None:
        conn = Connection(id=0, name="Test Connection")
        assert conn.length == 1

    def test_custom_length(self) -> None:
        conn = Connection(id=0, name="Long Passage", length=10)
        assert conn.length == 10

    def test_ways_property(self) -> None:
        conn = Connection(id=0, name="Passage")
        assert conn.ways == 0

        room_a = Room(id=1, name="Room A")
        room_b = Room(id=2, name="Room B")
        conn.add_connection(Direction.WEST, room_a)
        assert conn.ways == 1
        conn.add_connection(Direction.EAST, room_b)
        assert conn.ways == 2

    def test_connect_to_rooms(self) -> None:
        """A connection can link to rooms on both sides."""
        room_a = Room(id=0, name="Room A")
        room_b = Room(id=1, name="Room B")
        conn = Connection(id=2, name="Passage", length=5)

        conn.add_connection(Direction.WEST, room_a)
        conn.add_connection(Direction.EAST, room_b)

        assert conn.connection_count == 2
        assert conn.get_connection(Direction.WEST) == room_a
        assert conn.get_connection(Direction.EAST) == room_b

    def test_connect_to_connection(self) -> None:
        """A connection can connect to another connection (branching)."""
        conn_a = Connection(id=0, name="Main Passage", length=5)
        conn_b = Connection(id=1, name="Side Passage", length=3)

        conn_a.add_connection(Direction.NORTH, conn_b)
        conn_b.add_connection(Direction.SOUTH, conn_a)

        assert conn_a.get_connection(Direction.NORTH) == conn_b
        assert conn_b.get_connection(Direction.SOUTH) == conn_a

    def test_str(self) -> None:
        conn = Connection(id=5, name="Dark Passage", row=0, col=1, length=7)
        s = str(conn)
        assert "Dark Passage" in s
        assert "7" in s
        assert "way" in s


class TestMaze:
    def test_empty_maze(self) -> None:
        maze = Maze(rooms_wide=3, rooms_tall=3)
        assert maze.total_rooms == 9
        assert maze.all_rooms == []
        assert maze.all_connections == []

    def test_grid_dimensions(self) -> None:
        maze = Maze(rooms_wide=3, rooms_tall=4)
        assert maze.grid_width == 5  # 2*3 - 1
        assert maze.grid_height == 7  # 2*4 - 1

    def test_grid_dimensions_zero(self) -> None:
        maze = Maze(rooms_wide=0, rooms_tall=0)
        assert maze.grid_width == 0
        assert maze.grid_height == 0

    def test_get_room_logical(self) -> None:
        """get_room uses logical coordinates (not grid coordinates)."""
        r0 = Room(id=0, name="R0", row=0, col=0)
        r1 = Room(id=1, name="R1", row=0, col=2)
        r2 = Room(id=2, name="R2", row=2, col=0)
        r3 = Room(id=3, name="R3", row=2, col=2)
        grid: list[list[MazeNode | None]] = [
            [r0, None, r1],
            [None, None, None],
            [r2, None, r3],
        ]
        maze = Maze(rooms_wide=2, rooms_tall=2, grid=grid)
        assert maze.get_room(0, 0) is not None
        assert maze.get_room(0, 0).name == "R0"  # type: ignore[union-attr]
        assert maze.get_room(1, 1).name == "R3"  # type: ignore[union-attr]
        assert maze.get_room(5, 5) is None

    def test_all_nodes(self) -> None:
        r0 = Room(id=0, name="R0", row=0, col=0)
        r1 = Room(id=1, name="R1", row=0, col=2)
        c0 = Connection(id=2, name="C0", row=0, col=1, length=3)
        grid: list[list[MazeNode | None]] = [
            [r0, c0, r1],
        ]
        maze = Maze(rooms_wide=2, rooms_tall=1, grid=grid)
        assert len(maze.all_nodes) == 3
        assert len(maze.all_rooms) == 2
        assert len(maze.all_connections) == 1
        assert maze.total_nodes == 3

    def test_str(self) -> None:
        maze = Maze(rooms_wide=3, rooms_tall=4, name="Test Dungeon")
        s = str(maze)
        assert "Test Dungeon" in s
        assert "3x4" in s
        assert "connections" in s
