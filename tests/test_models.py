"""Tests for the data models."""

from dnd_maze_generator.models import (
    Connection,
    Direction,
    Maze,
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


class TestRoom:
    def _make_room(self, room_id: int = 0, name: str = "Test Room") -> Room:
        return Room(id=room_id, name=name, row=0, col=0)

    def test_default_attributes(self) -> None:
        room = self._make_room()
        assert room.owner == OwnerType.NONE
        assert room.treasure == TreasureType.NONE
        assert room.trap == TrapType.NONE
        assert room.connections == {}

    def test_add_connection(self) -> None:
        room_a = self._make_room(0, "Room A")
        room_b = self._make_room(1, "Room B")
        room_a.add_connection(Direction.NORTH, room_b, 5)

        assert room_a.connection_count == 1
        assert room_a.has_connection(Direction.NORTH)
        assert not room_a.has_connection(Direction.SOUTH)

    def test_get_connection(self) -> None:
        room_a = self._make_room(0, "Room A")
        room_b = self._make_room(1, "Room B")
        room_a.add_connection(Direction.EAST, room_b, 3)

        conn = room_a.get_connection(Direction.EAST)
        assert conn is not None
        assert conn.destination == room_b
        assert conn.length == 3
        assert conn.direction == Direction.EAST

        assert room_a.get_connection(Direction.WEST) is None

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

    def test_equality(self) -> None:
        room_a = self._make_room(0, "Room A")
        room_b = self._make_room(0, "Room B")
        room_c = self._make_room(1, "Room C")
        assert room_a == room_b  # Same ID
        assert room_a != room_c  # Different ID

    def test_hash(self) -> None:
        room_a = self._make_room(0)
        room_b = self._make_room(0)
        assert hash(room_a) == hash(room_b)


class TestConnection:
    def test_str(self) -> None:
        dest = Room(id=1, name="Destination", row=0, col=1)
        conn = Connection(direction=Direction.NORTH, destination=dest, length=5)
        s = str(conn)
        assert "N" in s
        assert "Destination" in s
        assert "5" in s


class TestMaze:
    def test_empty_maze(self) -> None:
        maze = Maze(width=3, height=3)
        assert maze.total_rooms == 9
        assert maze.all_rooms == []

    def test_get_room(self) -> None:
        rooms = [
            [Room(id=0, name="R0", row=0, col=0), Room(id=1, name="R1", row=0, col=1)],
            [Room(id=2, name="R2", row=1, col=0), Room(id=3, name="R3", row=1, col=1)],
        ]
        maze = Maze(width=2, height=2, rooms=rooms)
        assert maze.get_room(0, 0) is not None
        assert maze.get_room(0, 0).name == "R0"
        assert maze.get_room(1, 1).name == "R3"
        assert maze.get_room(5, 5) is None

    def test_str(self) -> None:
        maze = Maze(width=3, height=4, name="Test Dungeon")
        s = str(maze)
        assert "Test Dungeon" in s
        assert "3x4" in s
