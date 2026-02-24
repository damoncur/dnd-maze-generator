"""Tests for the display/visualization module."""

from dnd_maze_generator.display import (
    render_maze_map,
    render_maze_summary,
    render_node_details,
    render_room_details,
)
from dnd_maze_generator.generator import generate_maze
from dnd_maze_generator.models import (
    Corridor,
    Direction,
    Maze,
    OwnerType,
    Room,
    TrapType,
    TreasureType,
)


class TestRenderMazeMap:
    def test_renders_room_ids(self) -> None:
        maze = generate_maze(width=3, height=3, seed=42)
        output = render_maze_map(maze)
        # All room IDs should appear
        for i in range(9):
            assert str(i) in output

    def test_empty_maze(self) -> None:
        maze = Maze(width=0, height=0)
        output = render_maze_map(maze)
        assert output == "(empty maze)"


class TestRenderNodeDetails:
    def test_room_shows_all_attributes(self) -> None:
        room = Room(
            id=5,
            name="Dark Crypt",
            row=1,
            col=2,
            owner=OwnerType.SKELETON,
            treasure=TreasureType.GEMS,
            trap=TrapType.POISON_DART,
        )
        output = render_node_details(room)
        assert "Dark Crypt" in output
        assert "Skeleton" in output
        assert "Gems" in output
        assert "Poison Dart Trap" in output
        assert "(1, 2)" in output
        assert "Room" in output

    def test_corridor_shows_length(self) -> None:
        corridor = Corridor(id=10, name="Dark Passage", length=7)
        output = render_node_details(corridor)
        assert "Dark Passage" in output
        assert "7" in output
        assert "Corridor" in output

    def test_room_shows_corridor_neighbor(self) -> None:
        room = Room(id=0, name="Test Room")
        corridor = Corridor(id=1, name="Dark Passage", length=5)
        room.add_connection(Direction.EAST, corridor)

        output = render_node_details(room)
        assert "Corridor" in output
        assert "Dark Passage" in output

    def test_corridor_shows_room_neighbors(self) -> None:
        room_a = Room(id=0, name="Room A")
        room_b = Room(id=1, name="Room B")
        corridor = Corridor(id=2, name="Hallway", length=3)
        corridor.add_connection(Direction.WEST, room_a)
        corridor.add_connection(Direction.EAST, room_b)

        output = render_node_details(corridor)
        assert "Room A" in output
        assert "Room B" in output

    def test_isolated_node(self) -> None:
        room = Room(id=0, name="Lonely Room", row=0, col=0)
        output = render_node_details(room)
        assert "isolated" in output.lower() or "None" in output


class TestRenderRoomDetails:
    def test_is_wrapper_for_render_node_details(self) -> None:
        room = Room(
            id=5,
            name="Dark Crypt",
            row=1,
            col=2,
            owner=OwnerType.SKELETON,
        )
        assert render_room_details(room) == render_node_details(room)


class TestRenderMazeSummary:
    def test_contains_header_and_rooms(self) -> None:
        maze = generate_maze(width=3, height=3, seed=42, dungeon_name="Test Dungeon")
        output = render_maze_summary(maze)
        assert "Test Dungeon" in output
        assert "3 x 3" in output
        assert "9 rooms" in output
        assert "MAP" in output
        assert "ROOM DETAILS" in output
        assert "CORRIDOR DETAILS" in output
