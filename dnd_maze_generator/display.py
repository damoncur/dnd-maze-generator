"""Text-based display/visualization for the D&D Maze Generator."""

from __future__ import annotations

from .models import Direction, Maze, Room


def render_maze_map(maze: Maze) -> str:
    """Render a text-based map of the maze showing rooms and connections.

    Each room is shown as a box with its ID. Connections between rooms
    are shown with lines and their lengths.

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

            # Horizontal connection to the east
            if col_idx < maze.width - 1:
                east_conn = room.get_connection(Direction.EAST)
                if east_conn is not None:
                    length_str = str(east_conn.length).center(3)
                    top_line += f"  {length_str}"
                    mid_line += f"--{length_str}--"
                    bot_line += "     "
                else:
                    top_line += "     "
                    mid_line += "     "
                    bot_line += "     "

            # Vertical connection to the south
            if row_idx < maze.height - 1:
                south_conn = room.get_connection(Direction.SOUTH)
                if south_conn is not None:
                    center_offset = 3  # Center of the room box
                    pad = " " * center_offset
                    vert_line_1 += pad + "|" + " " * (room_width - center_offset - 1)
                    length_str = str(south_conn.length)
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


def render_room_details(room: Room) -> str:
    """Render detailed information about a single room."""
    parts: list[str] = []
    parts.append(f"=== [{room.id}] {room.name} ===")
    parts.append(f"  Position: ({room.row}, {room.col})")
    parts.append(f"  Owner:    {room.owner.value}")
    parts.append(f"  Treasure: {room.treasure.value}")
    parts.append(f"  Trap:     {room.trap.value}")

    if room.connections:
        parts.append(f"  Exits ({room.connection_count}):")
        for direction in [Direction.NORTH, Direction.EAST, Direction.SOUTH, Direction.WEST]:
            conn = room.get_connection(direction)
            if conn is not None:
                parts.append(
                    f"    {direction.value} -> [{conn.destination.id}] "
                    f"{conn.destination.name} (length: {conn.length})"
                )
    else:
        parts.append("  Exits: None (isolated room)")

    return "\n".join(parts)


def render_maze_summary(maze: Maze) -> str:
    """Render a full summary of the maze with map and all room details."""
    parts: list[str] = []

    # Header
    parts.append("=" * 60)
    parts.append(f"  {maze.name}")
    parts.append(f"  Size: {maze.width} x {maze.height} ({maze.total_rooms} rooms)")
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
        parts.append(render_room_details(room))

    parts.append("")
    parts.append("=" * 60)

    return "\n".join(parts)
