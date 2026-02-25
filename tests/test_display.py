"""Tests for the display/visualization module."""

from dnd_maze_generator.display import (
    _render_cell_3x3,
    render_maze_map,
    render_maze_summary,
    render_node_details,
    render_room_details,
)
from dnd_maze_generator.generator import generate_maze
from dnd_maze_generator.models import (
    Connection,
    Direction,
    Maze,
    OwnerType,
    Room,
    TrapType,
    TreasureType,
)


class TestRenderCell3x3:
    def test_none_is_solid_wall(self) -> None:
        tile = _render_cell_3x3(None)
        assert tile == [["#", "#", "#"], ["#", "#", "#"], ["#", "#", "#"]]

    def test_room_with_no_exits(self) -> None:
        room = Room(id=0, name="R", row=0, col=0)
        tile = _render_cell_3x3(room)
        # Corners are always walls
        assert tile[0][0] == "#"
        assert tile[0][2] == "#"
        assert tile[2][0] == "#"
        assert tile[2][2] == "#"
        # Centre is room ID char
        assert tile[1][1] == "0"
        # No exits => all cardinal edges are walls
        assert tile[0][1] == "#"
        assert tile[1][0] == "#"
        assert tile[1][2] == "#"
        assert tile[2][1] == "#"

    def test_room_with_exits(self) -> None:
        room = Room(id=3, name="R", row=0, col=0)
        conn = Connection(id=10, name="C", row=0, col=1)
        room.add_connection(Direction.EAST, conn)
        tile = _render_cell_3x3(room)
        # East exit should be open
        assert tile[1][2] == " "
        # Other exits still walls
        assert tile[0][1] == "#"
        assert tile[1][0] == "#"
        assert tile[2][1] == "#"

    def test_connection_centre_is_plus(self) -> None:
        conn = Connection(id=0, name="C", row=0, col=1)
        tile = _render_cell_3x3(conn)
        assert tile[1][1] == "+"


class TestRenderMazeMap:
    def test_renders_room_ids(self) -> None:
        maze = generate_maze(width=3, height=3, seed=42)
        output = render_maze_map(maze)
        # All room IDs 0-8 should appear somewhere
        for i in range(9):
            assert str(i) in output

    def test_empty_maze(self) -> None:
        maze = Maze(rooms_wide=0, rooms_tall=0)
        output = render_maze_map(maze)
        assert output == "(empty maze)"

    def test_entry_marked_with_star(self) -> None:
        maze = generate_maze(width=3, height=3, seed=42)
        output = render_maze_map(maze)
        assert "*" in output

    def test_opaque_corners(self) -> None:
        """Corners of every 3x3 tile should be '#'."""
        maze = generate_maze(width=2, height=2, seed=42)
        output = render_maze_map(maze)
        lines = output.split("\n")
        # Every tile's corner positions should be '#'
        gh = maze.grid_height
        gw = maze.grid_width
        for gr in range(gh):
            for gc in range(gw):
                # Top-left and top-right corners of each 3x3 tile
                assert lines[gr * 3][gc * 3] == "#"
                assert lines[gr * 3][gc * 3 + 2] == "#"
                # Bottom-left and bottom-right corners
                assert lines[gr * 3 + 2][gc * 3] == "#"
                assert lines[gr * 3 + 2][gc * 3 + 2] == "#"


class TestRenderNodeDetails:
    def test_room_shows_all_attributes(self) -> None:
        room = Room(
            id=5,
            name="Dark Crypt",
            row=2,
            col=4,
            owner=OwnerType.SKELETON,
            treasure=TreasureType.GEMS,
            trap=TrapType.POISON_DART,
        )
        output = render_node_details(room)
        assert "Dark Crypt" in output
        assert "Skeleton" in output
        assert "Gems" in output
        assert "Poison Dart Trap" in output
        assert "(2, 4)" in output
        assert "Room" in output

    def test_connection_shows_length_and_ways(self) -> None:
        conn = Connection(id=10, name="Dark Passage", row=0, col=1, length=7)
        room_a = Room(id=0, name="RA")
        room_b = Room(id=1, name="RB")
        conn.add_connection(Direction.WEST, room_a)
        conn.add_connection(Direction.EAST, room_b)
        output = render_node_details(conn)
        assert "Dark Passage" in output
        assert "7" in output
        assert "Connection" in output
        assert "Ways" in output or "2" in output

    def test_room_shows_connection_neighbor(self) -> None:
        room = Room(id=0, name="Test Room")
        conn = Connection(id=1, name="Dark Passage", length=5)
        room.add_connection(Direction.EAST, conn)

        output = render_node_details(room)
        assert "Connection" in output
        assert "Dark Passage" in output

    def test_connection_shows_room_neighbors(self) -> None:
        room_a = Room(id=0, name="Room A")
        room_b = Room(id=1, name="Room B")
        conn = Connection(id=2, name="Hallway", length=3)
        conn.add_connection(Direction.WEST, room_a)
        conn.add_connection(Direction.EAST, room_b)

        output = render_node_details(conn)
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
            row=2,
            col=4,
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
        assert "CONNECTION DETAILS" in output

    def test_shows_entry(self) -> None:
        maze = generate_maze(width=3, height=3, seed=42)
        output = render_maze_summary(maze)
        assert "Entry" in output
