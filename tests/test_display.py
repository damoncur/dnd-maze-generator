"""Tests for the display/visualization module."""

from dnd_maze_generator.display import (
    render_maze_map,
    render_maze_summary,
    render_room_details,
)
from dnd_maze_generator.generator import generate_maze
from dnd_maze_generator.models import Maze, OwnerType, Room, TrapType, TreasureType


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


class TestRenderRoomDetails:
    def test_shows_all_attributes(self) -> None:
        room = Room(
            id=5,
            name="Dark Crypt",
            row=1,
            col=2,
            owner=OwnerType.SKELETON,
            treasure=TreasureType.GEMS,
            trap=TrapType.POISON_DART,
        )
        output = render_room_details(room)
        assert "Dark Crypt" in output
        assert "Skeleton" in output
        assert "Gems" in output
        assert "Poison Dart Trap" in output
        assert "(1, 2)" in output

    def test_isolated_room(self) -> None:
        room = Room(id=0, name="Lonely Room", row=0, col=0)
        output = render_room_details(room)
        assert "isolated" in output.lower() or "None" in output


class TestRenderMazeSummary:
    def test_contains_header_and_rooms(self) -> None:
        maze = generate_maze(width=3, height=3, seed=42, dungeon_name="Test Dungeon")
        output = render_maze_summary(maze)
        assert "Test Dungeon" in output
        assert "3 x 3" in output
        assert "9 rooms" in output
        assert "MAP" in output
        assert "ROOM DETAILS" in output
