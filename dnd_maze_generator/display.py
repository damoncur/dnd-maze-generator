"""Text-based display/visualization for the D&D Maze Generator.

Each cell on the expanded grid is rendered as a 3x3 character tile:

    [#] [N] [#]        # = opaque corner (always wall)
    [W] [C] [E]        C = cell centre (Room ID or connection symbol)
    [#] [S] [#]        N/E/S/W = passage (space) or wall (#)

Corners (positions 1, 3, 7, 9 of the 3x3) are always opaque because
movement is restricted to cardinal directions only.
"""

from __future__ import annotations

from .models import Connection, Direction, Maze, MazeNode, Room

# Characters used in the 3x3 tile rendering
_WALL = "#"
_OPEN = " "


def _id_to_char(node_id: int) -> str:
    """Map a node ID to a single display character (0-9, A-Z, a-z)."""
    if node_id < 10:
        return str(node_id)
    if node_id < 36:
        return chr(ord("A") + node_id - 10)
    if node_id < 62:
        return chr(ord("a") + node_id - 36)
    return "?"


def _render_cell_3x3(cell: MazeNode | None) -> list[list[str]]:
    """Render a single cell as a 3x3 character grid.

    Layout (positions 1-9):
        1=[#]  2=[N exit]  3=[#]
        4=[W exit]  5=[centre]  6=[E exit]
        7=[#]  8=[S exit]  9=[#]
    """
    if cell is None:
        return [[_WALL] * 3, [_WALL] * 3, [_WALL] * 3]

    # Determine centre character
    if isinstance(cell, Room):
        centre = _id_to_char(cell.id)
    elif isinstance(cell, Connection):
        centre = "+"
    else:
        centre = "?"

    n = _OPEN if cell.has_connection(Direction.NORTH) else _WALL
    s = _OPEN if cell.has_connection(Direction.SOUTH) else _WALL
    e = _OPEN if cell.has_connection(Direction.EAST) else _WALL
    w = _OPEN if cell.has_connection(Direction.WEST) else _WALL

    return [
        [_WALL, n, _WALL],
        [w, centre, e],
        [_WALL, s, _WALL],
    ]


def render_maze_map(maze: Maze) -> str:
    """Render a 3x3-tile map of the maze.

    Each cell on the expanded grid becomes a 3x3 character block.
    Rooms show their ID character, connections show ``+``, and
    walls / empty cells are solid ``#`` blocks.

    The entry connection (maze start) is marked with ``*``.
    """
    if not maze.grid:
        return "(empty maze)"

    gh = len(maze.grid)
    gw = len(maze.grid[0]) if gh else 0

    # Build the output character grid
    out_h = gh * 3
    out_w = gw * 3
    out: list[list[str]] = [[_WALL] * out_w for _ in range(out_h)]

    for gr in range(gh):
        for gc in range(gw):
            cell = maze.grid[gr][gc]
            tile = _render_cell_3x3(cell)
            for tr in range(3):
                for tc in range(3):
                    out[gr * 3 + tr][gc * 3 + tc] = tile[tr][tc]

    # Mark the entry connection with *
    if maze.entry is not None:
        out[maze.entry.row * 3 + 1][maze.entry.col * 3 + 1] = "*"

    return "\n".join("".join(row) for row in out)


def render_node_details(node: MazeNode) -> str:
    """Render detailed information about any maze node (room or connection)."""
    parts: list[str] = []

    if isinstance(node, Room):
        parts.append(f"=== [Room {node.id}] {node.name} ===")
        parts.append(f"  Grid pos: ({node.row}, {node.col})")
        parts.append(f"  Owner:    {node.owner.value}")
        parts.append(f"  Treasure: {node.treasure.value}")
        parts.append(f"  Trap:     {node.trap.value}")
    elif isinstance(node, Connection):
        parts.append(f"=== [Connection {node.id}] {node.name} ===")
        parts.append(f"  Grid pos: ({node.row}, {node.col})")
        parts.append(f"  Length:   {node.length}")
        parts.append(f"  Ways:     {node.ways}")
    else:
        parts.append(f"=== [{node.id}] {node.name} ===")

    if node.connections:
        parts.append(f"  Exits ({node.connection_count}):")
        for direction in [Direction.NORTH, Direction.EAST, Direction.SOUTH, Direction.WEST]:
            neighbor = node.get_connection(direction)
            if neighbor is not None:
                node_type = "Connection" if isinstance(neighbor, Connection) else "Room"
                parts.append(
                    f"    {direction.value} -> [{node_type} {neighbor.id}] "
                    f"{neighbor.name}"
                )
    else:
        parts.append("  Exits: None (isolated node)")

    return "\n".join(parts)


def render_room_details(room: Room) -> str:
    """Render detailed information about a single room (convenience wrapper)."""
    return render_node_details(room)


def render_maze_summary(maze: Maze) -> str:
    """Render a full summary of the maze with map and all node details."""
    parts: list[str] = []

    # Header
    parts.append("=" * 60)
    parts.append(f"  {maze.name}")
    parts.append(
        f"  Size: {maze.rooms_wide} x {maze.rooms_tall} "
        f"({maze.total_rooms} rooms, {len(maze.all_connections)} connections)"
    )
    if maze.entry is not None:
        parts.append(f"  Entry: [{maze.entry.id}] {maze.entry.name}")
    parts.append("=" * 60)
    parts.append("")

    # Map
    parts.append("--- MAP ---")
    parts.append(render_maze_map(maze))
    parts.append("")

    # Room details
    parts.append("--- ROOM DETAILS ---")
    for room in maze.all_rooms:
        parts.append("")
        parts.append(render_node_details(room))

    # Connection details
    parts.append("")
    parts.append("--- CONNECTION DETAILS ---")
    for conn in maze.all_connections:
        parts.append("")
        parts.append(render_node_details(conn))

    parts.append("")
    parts.append("=" * 60)

    return "\n".join(parts)
