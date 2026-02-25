"""Command-line interface for the D&D Maze Generator."""

from __future__ import annotations

import argparse
import sys

from .display import render_maze_summary
from .generator import generate_maze


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        prog="dnd-maze-generator",
        description="Generate a D&D dungeon maze with rooms, traps, treasures, and monsters.",
    )

    parser.add_argument(
        "-W", "--width",
        type=int,
        default=5,
        help="Width of the maze grid (number of columns). Default: 5",
    )
    parser.add_argument(
        "-H", "--height",
        type=int,
        default=5,
        help="Height of the maze grid (number of rows). Default: 5",
    )
    parser.add_argument(
        "-s", "--seed",
        type=int,
        default=None,
        help="Random seed for reproducible mazes. Default: random",
    )
    parser.add_argument(
        "--min-length",
        type=int,
        default=1,
        help="Minimum connection traversal length. Default: 1",
    )
    parser.add_argument(
        "--max-length",
        type=int,
        default=10,
        help="Maximum connection traversal length. Default: 10",
    )
    parser.add_argument(
        "--owner-chance",
        type=float,
        default=0.4,
        help="Probability (0-1) a room has an owner/monster. Default: 0.4",
    )
    parser.add_argument(
        "--treasure-chance",
        type=float,
        default=0.3,
        help="Probability (0-1) a room has treasure. Default: 0.3",
    )
    parser.add_argument(
        "--trap-chance",
        type=float,
        default=0.25,
        help="Probability (0-1) a room has a trap. Default: 0.25",
    )
    parser.add_argument(
        "--extra-connections",
        type=float,
        default=0.1,
        help="Probability (0-1) of extra connections creating loops. Default: 0.1",
    )
    parser.add_argument(
        "-n", "--name",
        type=str,
        default="The Dungeon",
        help='Name of the dungeon. Default: "The Dungeon"',
    )

    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    """Main entry point for the CLI."""
    args = parse_args(argv)

    if args.width < 1 or args.height < 1:
        print("Error: Width and height must be at least 1.", file=sys.stderr)
        sys.exit(1)

    if args.min_length < 1:
        print("Error: Minimum connection length must be at least 1.", file=sys.stderr)
        sys.exit(1)

    if args.max_length < args.min_length:
        print(
            "Error: Maximum connection length must be >= minimum length.",
            file=sys.stderr,
        )
        sys.exit(1)

    maze = generate_maze(
        width=args.width,
        height=args.height,
        seed=args.seed,
        min_connection_length=args.min_length,
        max_connection_length=args.max_length,
        owner_chance=args.owner_chance,
        treasure_chance=args.treasure_chance,
        trap_chance=args.trap_chance,
        extra_connections=args.extra_connections,
        dungeon_name=args.name,
    )

    print(f"Grid: {maze.grid_height}x{maze.grid_width} "
          f"({maze.rooms_wide}x{maze.rooms_tall} rooms)")
    if maze.entry:
        print(f"Entry: [{maze.entry.id}] {maze.entry.name}")
    print()

    print(render_maze_summary(maze))


if __name__ == "__main__":
    main()
