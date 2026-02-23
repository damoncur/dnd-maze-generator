"""Tests for the maze generator."""

from dnd_maze_generator.generator import generate_maze
from dnd_maze_generator.models import Direction


class TestGenerateMaze:
    def test_basic_generation(self) -> None:
        maze = generate_maze(width=3, height=3, seed=42)
        assert maze.width == 3
        assert maze.height == 3
        assert maze.total_rooms == 9
        assert len(maze.all_rooms) == 9

    def test_reproducible_with_seed(self) -> None:
        maze1 = generate_maze(width=4, height=4, seed=123)
        maze2 = generate_maze(width=4, height=4, seed=123)

        for r1, r2 in zip(maze1.all_rooms, maze2.all_rooms):
            assert r1.owner == r2.owner
            assert r1.treasure == r2.treasure
            assert r1.trap == r2.trap
            assert r1.connection_count == r2.connection_count

    def test_all_rooms_connected(self) -> None:
        """The maze should be fully connected (all rooms reachable)."""
        maze = generate_maze(width=5, height=5, seed=42)
        start = maze.rooms[0][0]

        visited: set[int] = set()
        stack = [start]
        while stack:
            room = stack.pop()
            if room.id in visited:
                continue
            visited.add(room.id)
            for conn in room.connections.values():
                if conn.destination.id not in visited:
                    stack.append(conn.destination)

        assert len(visited) == maze.total_rooms

    def test_bidirectional_connections(self) -> None:
        """Every connection should have a matching reverse connection."""
        maze = generate_maze(width=4, height=4, seed=42)
        for room in maze.all_rooms:
            for direction, conn in room.connections.items():
                reverse = conn.destination.get_connection(direction.opposite)
                assert reverse is not None, (
                    f"Room {room.id} connects {direction.value} to {conn.destination.id}, "
                    f"but no reverse connection found"
                )
                assert reverse.destination == room

    def test_connection_lengths_in_range(self) -> None:
        maze = generate_maze(
            width=5, height=5, seed=42,
            min_connection_length=3, max_connection_length=7,
        )
        for room in maze.all_rooms:
            for conn in room.connections.values():
                assert 3 <= conn.length <= 7

    def test_rooms_have_unique_ids(self) -> None:
        maze = generate_maze(width=5, height=5, seed=42)
        ids = [r.id for r in maze.all_rooms]
        assert len(ids) == len(set(ids))

    def test_rooms_have_unique_names(self) -> None:
        maze = generate_maze(width=5, height=5, seed=42)
        names = [r.name for r in maze.all_rooms]
        assert len(names) == len(set(names))

    def test_max_four_connections(self) -> None:
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

    def test_linear_maze(self) -> None:
        maze = generate_maze(width=1, height=5, seed=42, extra_connections=0.0)
        assert maze.total_rooms == 5
        # In a 1-wide maze, rooms can only connect N/S
        for room in maze.all_rooms:
            for direction in room.connections:
                assert direction in (Direction.NORTH, Direction.SOUTH)

    def test_custom_dungeon_name(self) -> None:
        maze = generate_maze(width=3, height=3, seed=42, dungeon_name="Dragon's Lair")
        assert maze.name == "Dragon's Lair"

    def test_no_extra_connections(self) -> None:
        """With extra_connections=0, the maze is a spanning tree."""
        maze = generate_maze(width=5, height=5, seed=42, extra_connections=0.0)
        total_connections = sum(r.connection_count for r in maze.all_rooms)
        # A spanning tree of N nodes has N-1 edges, each counted twice (bidirectional)
        expected = (maze.total_rooms - 1) * 2
        assert total_connections == expected
