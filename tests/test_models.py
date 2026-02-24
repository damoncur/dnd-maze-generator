"""Tests for the data models."""

from dnd_maze_generator.models import (
    Corridor,
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
        node = MazeNode(id=5, name="Test Node")
        s = str(node)
        assert "5" in s
        assert "Test Node" in s

    def test_cross_type_equality(self) -> None:
        """Room and Corridor with same ID should be equal (both are MazeNodes)."""
        room = Room(id=0, name="Room")
        corridor = Corridor(id=0, name="Corridor", length=5)
        assert room == corridor


class TestRoom:
    def _make_room(self, room_id: int = 0, name: str = "Test Room") -> Room:
        return Room(id=room_id, name=name, row=0, col=0)

    def test_default_attributes(self) -> None:
        room = self._make_room()
        assert room.owner == OwnerType.NONE
        assert room.treasure == TreasureType.NONE
        assert room.trap == TrapType.NONE
        assert room.connections == {}

    def test_connect_to_corridor(self) -> None:
        room = self._make_room(0, "Room")
        corridor = Corridor(id=10, name="Corridor", length=5)
        room.add_connection(Direction.NORTH, corridor)

        assert room.connection_count == 1
        neighbor = room.get_connection(Direction.NORTH)
        assert neighbor is not None
        assert isinstance(neighbor, Corridor)
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


class TestCorridor:
    def test_default_length(self) -> None:
        corridor = Corridor(id=0, name="Test Corridor")
        assert corridor.length == 1

    def test_custom_length(self) -> None:
        corridor = Corridor(id=0, name="Long Corridor", length=10)
        assert corridor.length == 10

    def test_connect_to_rooms(self) -> None:
        """A corridor can connect to rooms on both sides."""
        room_a = Room(id=0, name="Room A")
        room_b = Room(id=1, name="Room B")
        corridor = Corridor(id=2, name="Corridor", length=5)

        corridor.add_connection(Direction.WEST, room_a)
        corridor.add_connection(Direction.EAST, room_b)

        assert corridor.connection_count == 2
        assert corridor.get_connection(Direction.WEST) == room_a
        assert corridor.get_connection(Direction.EAST) == room_b

    def test_connect_to_corridor(self) -> None:
        """A corridor can connect to another corridor (branching)."""
        corridor_a = Corridor(id=0, name="Main Corridor", length=5)
        corridor_b = Corridor(id=1, name="Side Corridor", length=3)

        corridor_a.add_connection(Direction.NORTH, corridor_b)
        corridor_b.add_connection(Direction.SOUTH, corridor_a)

        assert corridor_a.get_connection(Direction.NORTH) == corridor_b
        assert corridor_b.get_connection(Direction.SOUTH) == corridor_a

    def test_str(self) -> None:
        corridor = Corridor(id=5, name="Dark Passage", length=7)
        s = str(corridor)
        assert "Dark Passage" in s
        assert "7" in s


class TestMaze:
    def test_empty_maze(self) -> None:
        maze = Maze(width=3, height=3)
        assert maze.total_rooms == 9
        assert maze.all_rooms == []
        assert maze.corridors == []
        assert maze.total_nodes == 9  # Just rooms, no corridors yet

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

    def test_all_nodes(self) -> None:
        rooms = [
            [Room(id=0, name="R0"), Room(id=1, name="R1")],
        ]
        corridors = [Corridor(id=2, name="C0", length=3)]
        maze = Maze(width=2, height=1, rooms=rooms, corridors=corridors)
        assert len(maze.all_nodes) == 3
        assert maze.total_nodes == 3

    def test_str(self) -> None:
        maze = Maze(width=3, height=4, name="Test Dungeon")
        s = str(maze)
        assert "Test Dungeon" in s
        assert "3x4" in s
        assert "corridors" in s
