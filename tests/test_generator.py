"""Tests for the maze generator."""

from dnd_maze_generator.generator import generate_maze
from dnd_maze_generator.models import CellType, Connection, Direction, Maze, MazeNode, Room


class TestGenerateMaze:
    def test_basic_generation(self) -> None:
        maze = generate_maze(width=3, height=3, seed=42)
        assert maze.rooms_wide == 3
        assert maze.rooms_tall == 3
        assert maze.total_rooms == 9
        assert len(maze.all_rooms) == 9

    def test_grid_dimensions(self) -> None:
        maze = generate_maze(width=3, height=3, seed=42)
        assert maze.grid_width == 5  # 2*3-1
        assert maze.grid_height == 5  # 2*3-1

    def test_connections_created(self) -> None:
        """Each edge between rooms should create a connection node."""
        maze = generate_maze(width=3, height=3, seed=42, extra_connections=0.0)
        # A spanning tree of 9 rooms has 8 edges = 8 connections
        assert len(maze.all_connections) == 8

    def test_rooms_at_even_positions(self) -> None:
        """Rooms must sit at even-row, even-col positions on the grid."""
        maze = generate_maze(width=3, height=3, seed=42)
        for room in maze.all_rooms:
            assert room.row % 2 == 0, f"Room {room.id} row {room.row} is odd"
            assert room.col % 2 == 0, f"Room {room.id} col {room.col} is odd"

    def test_connections_at_mixed_parity(self) -> None:
        """Connections must sit at mixed-parity positions on the grid."""
        maze = generate_maze(width=3, height=3, seed=42)
        for conn in maze.all_connections:
            parity = (conn.row % 2, conn.col % 2)
            assert parity in ((0, 1), (1, 0)), (
                f"Connection {conn.id} at ({conn.row},{conn.col}) has bad parity"
            )

    def test_rooms_connect_to_connections(self) -> None:
        """Rooms should connect to connection nodes, not directly to other rooms."""
        maze = generate_maze(width=3, height=3, seed=42)
        for room in maze.all_rooms:
            for neighbor in room.connections.values():
                assert isinstance(neighbor, Connection), (
                    f"Room {room.id} connects directly to {type(neighbor).__name__} "
                    f"{neighbor.id}, expected Connection"
                )

    def test_connections_connect_to_rooms(self) -> None:
        """Each spanning-tree connection should have exactly 2 exits."""
        maze = generate_maze(width=3, height=3, seed=42, extra_connections=0.0)
        for conn in maze.all_connections:
            assert conn.connection_count == 2

    def test_connection_ways(self) -> None:
        """The ways property should match connection_count."""
        maze = generate_maze(width=3, height=3, seed=42)
        for conn in maze.all_connections:
            assert conn.ways == conn.connection_count

    def test_entry_is_connection(self) -> None:
        """Maze entry point must be a Connection node."""
        maze = generate_maze(width=3, height=3, seed=42)
        assert maze.entry is not None
        assert isinstance(maze.entry, Connection)

    def test_reproducible_with_seed(self) -> None:
        maze1 = generate_maze(width=4, height=4, seed=123)
        maze2 = generate_maze(width=4, height=4, seed=123)

        for r1, r2 in zip(maze1.all_rooms, maze2.all_rooms):
            assert r1.owner == r2.owner
            assert r1.treasure == r2.treasure
            assert r1.trap == r2.trap
            assert r1.connection_count == r2.connection_count

        assert len(maze1.all_connections) == len(maze2.all_connections)
        for c1, c2 in zip(maze1.all_connections, maze2.all_connections):
            assert c1.length == c2.length

    def test_all_rooms_reachable(self) -> None:
        """All rooms should be reachable by traversing through connections."""
        maze = generate_maze(width=5, height=5, seed=42)
        start = maze.all_rooms[0]

        visited: set[int] = set()
        stack: list[MazeNode] = [start]
        while stack:
            node = stack.pop()
            if node.id in visited:
                continue
            visited.add(node.id)
            for neighbor in node.connections.values():
                if neighbor.id not in visited:
                    stack.append(neighbor)

        # All rooms and connections should be reachable
        assert len(visited) == maze.total_nodes

    def test_bidirectional_connections(self) -> None:
        """Every connection should have a matching reverse connection."""
        maze = generate_maze(width=4, height=4, seed=42)
        for node in maze.all_nodes:
            for direction, neighbor in node.connections.items():
                reverse = neighbor.get_connection(direction.opposite)
                assert reverse is not None, (
                    f"Node {node.id} connects {direction.value} to {neighbor.id}, "
                    f"but no reverse connection found"
                )
                assert reverse == node

    def test_connection_lengths_in_range(self) -> None:
        maze = generate_maze(
            width=5, height=5, seed=42,
            min_connection_length=3, max_connection_length=7,
        )
        for conn in maze.all_connections:
            assert 3 <= conn.length <= 7

    def test_all_nodes_have_unique_ids(self) -> None:
        maze = generate_maze(width=5, height=5, seed=42)
        ids = [n.id for n in maze.all_nodes]
        assert len(ids) == len(set(ids))

    def test_rooms_have_unique_names(self) -> None:
        maze = generate_maze(width=5, height=5, seed=42)
        names = [r.name for r in maze.all_rooms]
        assert len(names) == len(set(names))

    def test_max_four_connections_per_room(self) -> None:
        """Each room should have at most 4 connections (N, E, S, W)."""
        maze = generate_maze(width=5, height=5, seed=42, extra_connections=0.5)
        for room in maze.all_rooms:
            assert room.connection_count <= 4

    def test_at_least_one_connection(self) -> None:
        """Every room should have at least one connection."""
        maze = generate_maze(width=5, height=5, seed=42)
        for room in maze.all_rooms:
            assert room.connection_count >= 1

    def test_single_room_maze(self) -> None:
        maze = generate_maze(width=1, height=1, seed=42)
        assert maze.total_rooms == 1
        assert len(maze.all_rooms) == 1
        assert maze.all_rooms[0].connection_count == 0
        assert len(maze.all_connections) == 0

    def test_linear_maze(self) -> None:
        maze = generate_maze(width=1, height=5, seed=42, extra_connections=0.0)
        assert maze.total_rooms == 5
        # In a 1-wide maze, rooms can only connect N/S (via connections)
        for room in maze.all_rooms:
            for direction in room.connections:
                assert direction in (Direction.NORTH, Direction.SOUTH)

    def test_custom_dungeon_name(self) -> None:
        maze = generate_maze(width=3, height=3, seed=42, dungeon_name="Dragon's Lair")
        assert maze.name == "Dragon's Lair"

    def test_no_extra_connections(self) -> None:
        """With extra_connections=0, maze has exactly N-1 connections (spanning tree)."""
        maze = generate_maze(width=5, height=5, seed=42, extra_connections=0.0)
        expected = maze.total_rooms - 1
        assert len(maze.all_connections) == expected

    def test_connection_chain(self) -> None:
        """Verify Room -> Connection -> Room chain structure."""
        maze = generate_maze(width=2, height=1, seed=42, extra_connections=0.0)
        room_a = maze.get_room(0, 0)
        room_b = maze.get_room(0, 1)
        assert room_a is not None
        assert room_b is not None

        assert len(maze.all_connections) == 1
        conn = maze.all_connections[0]

        # The connection should have exactly 2 exits to the two rooms
        assert conn.connection_count == 2
        neighbors = set(conn.connections.values())
        assert room_a in neighbors
        assert room_b in neighbors

    def test_grid_cell_types(self) -> None:
        """Verify cell types match their grid positions."""
        maze = generate_maze(width=3, height=3, seed=42)
        for gr in range(maze.grid_height):
            for gc in range(maze.grid_width):
                cell = maze.get_cell(gr, gc)
                expected = Maze.cell_type_at(gr, gc)
                if expected == CellType.WALL:
                    assert cell is None, f"Wall at ({gr},{gc}) is not None"
                elif expected == CellType.ROOM:
                    assert isinstance(cell, Room), f"Expected Room at ({gr},{gc})"
                elif cell is not None:
                    assert isinstance(cell, Connection), (
                        f"Expected Connection at ({gr},{gc})"
                    )
