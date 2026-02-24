"""Text-based display/visualization for the D&D Maze Generator."""

from __future__ import annotations

from .models import Corridor, Direction, Maze, MazeNode, Room


def _get_corridor_between(room: Room, direction: Direction) -> Corridor | None:
    """Get the corridor node between a room and its neighbor in a direction.

    Returns the Corridor if the room connects to one in that direction, else None.
    """
    neighbor = room.get_connection(direction)
    if isinstance(neighbor, Corridor):
        return neighbor
    return None


def render_maze_map(maze: Maze) -> str:
    """Render a text-based map of the maze showing rooms and corridor connections.

    Each room is shown as a box with its ID. Corridors between rooms are
    shown with lines and their lengths.

    Example output for a 3x3 maze:
        +-----+  3  +-----+     +-----+
        |  0  |-----|  1  |     |  2  |
        +-----+     +-----+     +-----+
           |                       |
           5                       2
           |                       |
        +-----+     +-----+  7  +-----+
        |  3  |     |  4  |-----|  5  |
        +-----+     +-----+     +-----+
    """
    if not maze.rooms:
        return "(empty maze)"

    lines: list[str] = []
    room_width = 7  # Width of each room box: +-----+
    h_gap = 5  # Horizontal gap between rooms for connection labels

    for row_idx in range(maze.height):
        # Top border of room boxes
        top_line = ""
        # Room content line (IDs)
        mid_line = ""
        # Bottom border of room boxes
        bot_line = ""
        # Vertical connection lines (below this row)
        vert_line_1 = ""  # The pipe |
        vert_line_2 = ""  # The length number
        vert_line_3 = ""  # The pipe |

        for col_idx in range(maze.width):
            room = maze.rooms[row_idx][col_idx]
            room_label = str(room.id).center(5)

            top_line += "+-----+"
            mid_line += f"|{room_label}|"
            bot_line += "+-----+"

            # Horizontal connection to the east (via corridor)
            if col_idx < maze.width - 1:
                corridor = _get_corridor_between(room, Direction.EAST)
                if corridor is not None:
                    length_str = str(corridor.length).center(3)
                    top_line += f"  {length_str}"
                    mid_line += f"--{length_str}--"
                    bot_line += "     "
                else:
                    top_line += "     "
                    mid_line += "     "
                    bot_line += "     "

            # Vertical connection to the south (via corridor)
            if row_idx < maze.height - 1:
                corridor = _get_corridor_between(room, Direction.SOUTH)
                if corridor is not None:
                    center_offset = 3  # Center of the room box
                    pad = " " * center_offset
                    vert_line_1 += pad + "|" + " " * (room_width - center_offset - 1)
                    length_str = str(corridor.length)
                    remaining = room_width - center_offset - len(length_str)
                    vert_line_2 += pad + length_str + " " * remaining
                    vert_line_3 += pad + "|" + " " * (room_width - center_offset - 1)
                else:
                    vert_line_1 += " " * room_width
                    vert_line_2 += " " * room_width
                    vert_line_3 += " " * room_width

                # Gap for horizontal connection area
                if col_idx < maze.width - 1:
                    vert_line_1 += " " * h_gap
                    vert_line_2 += " " * h_gap
                    vert_line_3 += " " * h_gap

        lines.append(top_line)
        lines.append(mid_line)
        lines.append(bot_line)

        if row_idx < maze.height - 1:
            lines.append(vert_line_1)
            lines.append(vert_line_2)
            lines.append(vert_line_3)

    return "\n".join(lines)


def render_node_details(node: MazeNode) -> str:
    """Render detailed information about any maze node (room or corridor)."""
    parts: list[str] = []

    if isinstance(node, Room):
        parts.append(f"=== [Room {node.id}] {node.name} ===")
        parts.append(f"  Position: ({node.row}, {node.col})")
        parts.append(f"  Owner:    {node.owner.value}")
        parts.append(f"  Treasure: {node.treasure.value}")
        parts.append(f"  Trap:     {node.trap.value}")
    elif isinstance(node, Corridor):
        parts.append(f"=== [Corridor {node.id}] {node.name} ===")
        parts.append(f"  Length:   {node.length}")
    else:
        parts.append(f"=== [{node.id}] {node.name} ===")

    if node.connections:
        parts.append(f"  Exits ({node.connection_count}):")
        for direction in [Direction.NORTH, Direction.EAST, Direction.SOUTH, Direction.WEST]:
            neighbor = node.get_connection(direction)
            if neighbor is not None:
                node_type = "Corridor" if isinstance(neighbor, Corridor) else "Room"
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
        f"  Size: {maze.width} x {maze.height} "
        f"({maze.total_rooms} rooms, {len(maze.corridors)} corridors)"
    )
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

    # Corridor details
    parts.append("")
    parts.append("--- CORRIDOR DETAILS ---")
    for corridor in maze.corridors:
        parts.append("")
        parts.append(render_node_details(corridor))

    parts.append("")
    parts.append("=" * 60)

    return "\n".join(parts)
