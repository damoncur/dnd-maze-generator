"""Tests for the CLI module."""

from dnd_maze_generator.cli import parse_args


class TestParseArgs:
    def test_defaults(self) -> None:
        args = parse_args([])
        assert args.width == 5
        assert args.height == 5
        assert args.seed is None
        assert args.min_length == 1
        assert args.max_length == 10
        assert args.owner_chance == 0.4
        assert args.treasure_chance == 0.3
        assert args.trap_chance == 0.25
        assert args.extra_connections == 0.1
        assert args.name == "The Dungeon"

    def test_custom_size(self) -> None:
        args = parse_args(["-W", "10", "-H", "8"])
        assert args.width == 10
        assert args.height == 8

    def test_seed(self) -> None:
        args = parse_args(["-s", "42"])
        assert args.seed == 42

    def test_connection_lengths(self) -> None:
        args = parse_args(["--min-length", "3", "--max-length", "7"])
        assert args.min_length == 3
        assert args.max_length == 7

    def test_custom_name(self) -> None:
        args = parse_args(["-n", "Dragon's Lair"])
        assert args.name == "Dragon's Lair"

    def test_chances(self) -> None:
        args = parse_args([
            "--owner-chance", "0.5",
            "--treasure-chance", "0.6",
            "--trap-chance", "0.7",
            "--extra-connections", "0.2",
        ])
        assert args.owner_chance == 0.5
        assert args.treasure_chance == 0.6
        assert args.trap_chance == 0.7
        assert args.extra_connections == 0.2
