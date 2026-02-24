"""Tests for the maze generator."""

from dnd_maze_generator.generator import generate_maze
from dnd_maze_generator.models import Corridor, Direction, MazeNode


class TestGenerateMaze:
    def test_basic_generation(self) -> None:
        maze = generate_maze(width=3, height=3, seed=42)
        assert maze.width == 3
        assert maze.height == 3
        assert maze.total_rooms == 9
        assert len(maze.all_rooms) == 9

    def test_corridors_created(self) -> None:
        """Each edge between rooms should create a corridor node."""
        maze = generate_maze(width=3, height=3, seed=42, extra_connections=0.0)
        # A spanning tree of 9 rooms has 8 edges = 8 corridors
        assert len(maze.corridors) == 8

    def test_rooms_connect_to_corridors(self) -> None:
        """Rooms should connect to corridor nodes, not directly to other rooms."""
        maze = generate_maze(width=3, height=3, seed=42)
        for room in maze.all_rooms:
            for neighbor in room.connections.values():
                assert isinstance(neighbor, Corridor), (
                    f"Room {room.id} connects directly to {type(neighbor).__name__} "
                    f"{neighbor.id}, expected Corridor"
                )

    def test_corridors_connect_to_rooms(self) -> None:
        """Each corridor should connect to exactly two nodes in opposite directions."""
        maze = generate_maze(width=3, height=3, seed=42, extra_connections=0.0)
        for corridor in maze.corridors:
            assert corridor.connection_count == 2

    def test_reproducible_with_seed(self) -> None:
        maze1 = generate_maze(width=4, height=4, seed=123)
        maze2 = generate_maze(width=4, height=4, seed=123)

        for r1, r2 in zip(maze1.all_rooms, maze2.all_rooms):
            assert r1.owner == r2.owner
            assert r1.treasure == r2.treasure
            assert r1.trap == r2.trap
            assert r1.connection_count == r2.connection_count

        assert len(maze1.corridors) == len(maze2.corridors)
        for c1, c2 in zip(maze1.corridors, maze2.corridors):
            assert c1.length == c2.length

    def test_all_rooms_reachable(self) -> None:
        """All rooms should be reachable by traversing through corridors."""
        maze = generate_maze(width=5, height=5, seed=42)
        start = maze.rooms[0][0]

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

        # All rooms and corridors should be reachable
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

    def test_corridor_lengths_in_range(self) -> None:
        maze = generate_maze(
            width=5, height=5, seed=42,
            min_connection_length=3, max_connection_length=7,
        )
        for corridor in maze.corridors:
            assert 3 <= corridor.length <= 7

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
        assert len(maze.corridors) == 0

    def test_linear_maze(self) -> None:
        maze = generate_maze(width=1, height=5, seed=42, extra_connections=0.0)
        assert maze.total_rooms == 5
        # In a 1-wide maze, rooms can only connect N/S (via corridors)
        for room in maze.all_rooms:
            for direction in room.connections:
                assert direction in (Direction.NORTH, Direction.SOUTH)

    def test_custom_dungeon_name(self) -> None:
        maze = generate_maze(width=3, height=3, seed=42, dungeon_name="Dragon's Lair")
        assert maze.name == "Dragon's Lair"

    def test_no_extra_connections(self) -> None:
        """With extra_connections=0, the maze has exactly N-1 corridors (spanning tree)."""
        maze = generate_maze(width=5, height=5, seed=42, extra_connections=0.0)
        expected_corridors = maze.total_rooms - 1
        assert len(maze.corridors) == expected_corridors

    def test_corridor_chain(self) -> None:
        """Verify Room -> Corridor -> Room chain structure."""
        maze = generate_maze(width=2, height=1, seed=42, extra_connections=0.0)
        room_a = maze.rooms[0][0]
        room_b = maze.rooms[0][1]

        # One of them should connect east, the other west
        assert len(maze.corridors) == 1
        corridor = maze.corridors[0]

        # The corridor should have exactly 2 connections to the two rooms
        assert corridor.connection_count == 2
        neighbors = set(corridor.connections.values())
        assert room_a in neighbors
        assert room_b in neighbors
