"""Panda3D-based 3D visualization of a generated maze.

Renders rooms, corridors, doors, and walls as 3D geometry.
Camera is controlled with WASD + mouse for first-person exploration.
"""

from __future__ import annotations

from typing import Optional

from direct.showbase.ShowBase import ShowBase  # type: ignore[import-untyped]
from panda3d.core import (  # type: ignore[import-untyped]
    AmbientLight,
    CardMaker,
    ClockObject,
    DirectionalLight,
    LColor,
    LVector3,
    LVertex,
    NodePath,
    PointLight,
    TextNode,
    TransparencyAttrib,
    WindowProperties,
)

from .models import Connection, Direction, DoorType, Maze, MazeNode, Room

# Dimensions for each grid cell in 3D space
CELL_SIZE = 6.0
WALL_HEIGHT = 4.0

# Colours
COLOR_ROOM_FLOOR = LColor(0.55, 0.45, 0.35, 1.0)  # warm stone
COLOR_CORRIDOR_FLOOR = LColor(0.40, 0.35, 0.30, 1.0)  # darker stone
COLOR_WALL = LColor(0.35, 0.30, 0.25, 1.0)  # dark stone
COLOR_CEILING = LColor(0.25, 0.22, 0.18, 1.0)  # dark ceiling

# Door colours by type
DOOR_COLORS: dict[DoorType, LColor] = {
    DoorType.WOODEN: LColor(0.55, 0.35, 0.15, 1.0),
    DoorType.IRON: LColor(0.50, 0.50, 0.55, 1.0),
    DoorType.STEEL: LColor(0.70, 0.70, 0.75, 1.0),
    DoorType.LARGE_ROCK: LColor(0.40, 0.38, 0.35, 1.0),
    DoorType.HIDDEN: LColor(0.35, 0.30, 0.25, 0.5),  # semi-transparent
}


def _node_key(wx: float, wy: float) -> str:
    """Create a short unique key from world coordinates."""
    return f"{wx:.0f}_{wy:.0f}"


def _make_quad(
    name: str,
    ll: LVertex,
    lr: LVertex,
    ur: LVertex,
    ul: LVertex,
    color: LColor,
) -> NodePath:
    """Create a colored quad from four explicit 3D corner vertices.

    Vertices should be specified in counter-clockwise order when viewed
    from the front face (the side the normal points toward).

    Args:
        name: Node name.
        ll: Lower-left corner.
        lr: Lower-right corner.
        ur: Upper-right corner.
        ul: Upper-left corner.
        color: RGBA color.
    """
    cm = CardMaker(name)
    cm.set_frame(ll, lr, ur, ul)
    cm.set_color(color)
    cm.set_has_normals(True)
    node = cm.generate()
    np = NodePath(node)
    np.set_two_sided(True)
    return np


def _grid_to_world(row: int, col: int) -> tuple[float, float]:
    """Convert grid coordinates to world X, Y position."""
    x = col * CELL_SIZE
    y = -row * CELL_SIZE  # negate so north is +Y visually
    return x, y


class MazeViewer(ShowBase):  # type: ignore[misc]
    """Panda3D application that renders a maze in 3D.

    Rooms are rendered as open boxes with floors, walls, and ceilings.
    Corridors are rendered similarly but with a different floor colour.
    Doors appear as coloured planes at room exits.
    Camera uses WASD + mouse for first-person navigation.
    """

    def __init__(self, maze: Maze) -> None:
        super().__init__()
        self.maze = maze
        self.movement_speed = 15.0
        self.mouse_sensitivity = 0.3
        self.heading = 0.0
        self.pitch = 0.0

        # Current node for maze traversal (IJKM keys)
        self._current_node: Optional[MazeNode] = None
        self._location_text: Optional[object] = None  # OnscreenText

        self._setup_window()
        self._setup_lighting()
        self._build_maze()
        self._setup_camera()
        self._setup_controls()
        self._add_hud()

    def _setup_window(self) -> None:
        """Configure window properties."""
        props = WindowProperties()
        props.set_title(f"D&D Maze: {self.maze.name}")
        props.set_size(1280, 720)
        self.win.request_properties(props)
        self.set_background_color(0.05, 0.05, 0.1, 1.0)  # dark blue-black

    def _setup_lighting(self) -> None:
        """Set up ambient and directional lighting."""
        # Bright ambient light so everything is visible
        ambient = AmbientLight("ambient")
        ambient.set_color(LColor(0.45, 0.45, 0.45, 1.0))
        ambient_np = self.render.attach_new_node(ambient)
        self.render.set_light(ambient_np)

        # Directional light from above
        sun = DirectionalLight("sun")
        sun.set_color(LColor(0.6, 0.55, 0.5, 1.0))
        sun_np = self.render.attach_new_node(sun)
        sun_np.set_hpr(45, -60, 0)
        self.render.set_light(sun_np)

    def _build_maze(self) -> None:
        """Build the 3D maze geometry from the maze grid."""
        maze_root = self.render.attach_new_node("maze_root")

        for row_idx, row in enumerate(self.maze.grid):
            for col_idx, cell in enumerate(row):
                if cell is None:
                    continue
                wx, wy = _grid_to_world(row_idx, col_idx)
                self._build_cell(maze_root, cell, wx, wy)

    def _build_cell(
        self, parent: NodePath, node: MazeNode, wx: float, wy: float
    ) -> None:
        """Build floor, walls, ceiling, and doors for one grid cell."""
        cell_np = parent.attach_new_node(f"cell_{node.id}")

        is_room = isinstance(node, Room)
        floor_color = COLOR_ROOM_FLOOR if is_room else COLOR_CORRIDOR_FLOOR
        half = CELL_SIZE / 2.0

        # Floor: flat quad at z=0 in the XY plane
        floor = _make_quad(
            f"floor_{node.id}",
            LVertex(wx - half, wy - half, 0),
            LVertex(wx + half, wy - half, 0),
            LVertex(wx + half, wy + half, 0),
            LVertex(wx - half, wy + half, 0),
            floor_color,
        )
        floor.reparent_to(cell_np)

        # Ceiling: flat quad at z=WALL_HEIGHT
        ceiling = _make_quad(
            f"ceiling_{node.id}",
            LVertex(wx - half, wy + half, WALL_HEIGHT),
            LVertex(wx + half, wy + half, WALL_HEIGHT),
            LVertex(wx + half, wy - half, WALL_HEIGHT),
            LVertex(wx - half, wy - half, WALL_HEIGHT),
            COLOR_CEILING,
        )
        ceiling.reparent_to(cell_np)

        # Walls on sides without exits
        all_dirs = [Direction.NORTH, Direction.SOUTH, Direction.EAST, Direction.WEST]
        for direction in all_dirs:
            if node.has_connection(direction):
                # There is an exit here -- check for doors
                if is_room:
                    assert isinstance(node, Room)
                    door = node.get_door(direction)
                    if door is not None:
                        self._build_door(cell_np, wx, wy, direction, door.door_type)
                continue
            self._build_wall(cell_np, wx, wy, direction)

        # Add a floating label with the node type and ID
        self._build_label(cell_np, node, wx, wy)

        # Add a point light inside rooms for atmosphere
        if is_room:
            plight = PointLight(f"light_{node.id}")
            plight.set_color(LColor(0.8, 0.7, 0.5, 1.0))
            plight.set_attenuation((1.0, 0.05, 0.01))
            plight_np = cell_np.attach_new_node(plight)
            plight_np.set_pos(wx, wy, WALL_HEIGHT * 0.8)
            self.render.set_light(plight_np)

    def _build_wall(
        self, cell_np: NodePath, wx: float, wy: float, direction: Direction
    ) -> None:
        """Place a wall on the given side of a cell using explicit vertices."""
        half = CELL_SIZE / 2.0
        h = WALL_HEIGHT
        key = _node_key(wx, wy)

        if direction == Direction.NORTH:
            wall = _make_quad(
                f"wall_N_{key}",
                LVertex(wx + half, wy + half, 0),
                LVertex(wx - half, wy + half, 0),
                LVertex(wx - half, wy + half, h),
                LVertex(wx + half, wy + half, h),
                COLOR_WALL,
            )
        elif direction == Direction.SOUTH:
            wall = _make_quad(
                f"wall_S_{key}",
                LVertex(wx - half, wy - half, 0),
                LVertex(wx + half, wy - half, 0),
                LVertex(wx + half, wy - half, h),
                LVertex(wx - half, wy - half, h),
                COLOR_WALL,
            )
        elif direction == Direction.EAST:
            wall = _make_quad(
                f"wall_E_{key}",
                LVertex(wx + half, wy - half, 0),
                LVertex(wx + half, wy + half, 0),
                LVertex(wx + half, wy + half, h),
                LVertex(wx + half, wy - half, h),
                COLOR_WALL,
            )
        else:
            wall = _make_quad(
                f"wall_W_{key}",
                LVertex(wx - half, wy + half, 0),
                LVertex(wx - half, wy - half, 0),
                LVertex(wx - half, wy - half, h),
                LVertex(wx - half, wy + half, h),
                COLOR_WALL,
            )
        wall.reparent_to(cell_np)

    def _build_door(
        self,
        cell_np: NodePath,
        wx: float,
        wy: float,
        direction: Direction,
        door_type: DoorType,
    ) -> None:
        """Place a door and lintel on the given side of a cell."""
        color = DOOR_COLORS.get(door_type, DOOR_COLORS[DoorType.WOODEN])
        half = CELL_SIZE / 2.0
        dw = CELL_SIZE * 0.35  # half door width
        dh = WALL_HEIGHT * 0.8  # door height
        lintel_bottom = dh
        lintel_top = WALL_HEIGHT
        key = _node_key(wx, wy)

        if direction == Direction.NORTH:
            y = wy + half
            door = _make_quad(
                f"door_N_{key}",
                LVertex(wx + dw, y, 0),
                LVertex(wx - dw, y, 0),
                LVertex(wx - dw, y, dh),
                LVertex(wx + dw, y, dh),
                color,
            )
            if lintel_top - lintel_bottom > 0.1:
                lintel = _make_quad(
                    f"lintel_N_{key}",
                    LVertex(wx + half, y, lintel_bottom),
                    LVertex(wx - half, y, lintel_bottom),
                    LVertex(wx - half, y, lintel_top),
                    LVertex(wx + half, y, lintel_top),
                    COLOR_WALL,
                )
                lintel.reparent_to(cell_np)
        elif direction == Direction.SOUTH:
            y = wy - half
            door = _make_quad(
                f"door_S_{key}",
                LVertex(wx - dw, y, 0),
                LVertex(wx + dw, y, 0),
                LVertex(wx + dw, y, dh),
                LVertex(wx - dw, y, dh),
                color,
            )
            if lintel_top - lintel_bottom > 0.1:
                lintel = _make_quad(
                    f"lintel_S_{key}",
                    LVertex(wx - half, y, lintel_bottom),
                    LVertex(wx + half, y, lintel_bottom),
                    LVertex(wx + half, y, lintel_top),
                    LVertex(wx - half, y, lintel_top),
                    COLOR_WALL,
                )
                lintel.reparent_to(cell_np)
        elif direction == Direction.EAST:
            x = wx + half
            door = _make_quad(
                f"door_E_{key}",
                LVertex(x, wy - dw, 0),
                LVertex(x, wy + dw, 0),
                LVertex(x, wy + dw, dh),
                LVertex(x, wy - dw, dh),
                color,
            )
            if lintel_top - lintel_bottom > 0.1:
                lintel = _make_quad(
                    f"lintel_E_{key}",
                    LVertex(x, wy - half, lintel_bottom),
                    LVertex(x, wy + half, lintel_bottom),
                    LVertex(x, wy + half, lintel_top),
                    LVertex(x, wy - half, lintel_top),
                    COLOR_WALL,
                )
                lintel.reparent_to(cell_np)
        else:
            x = wx - half
            door = _make_quad(
                f"door_W_{key}",
                LVertex(x, wy + dw, 0),
                LVertex(x, wy - dw, 0),
                LVertex(x, wy - dw, dh),
                LVertex(x, wy + dw, dh),
                color,
            )
            if lintel_top - lintel_bottom > 0.1:
                lintel = _make_quad(
                    f"lintel_W_{key}",
                    LVertex(x, wy + half, lintel_bottom),
                    LVertex(x, wy - half, lintel_bottom),
                    LVertex(x, wy - half, lintel_top),
                    LVertex(x, wy + half, lintel_top),
                    COLOR_WALL,
                )
                lintel.reparent_to(cell_np)

        if door_type == DoorType.HIDDEN:
            door.set_transparency(TransparencyAttrib.MAlpha)
        door.reparent_to(cell_np)

    def _build_label(
        self, cell_np: NodePath, node: MazeNode, wx: float, wy: float
    ) -> None:
        """Add a floating 3D text label showing the node type and ID."""
        if isinstance(node, Room):
            label_text = f"Room {node.id}"
            fg = LColor(1.0, 1.0, 0.6, 1.0)  # warm yellow
        elif isinstance(node, Connection):
            label_text = f"Cor {node.id}"
            fg = LColor(0.6, 0.8, 1.0, 1.0)  # light blue
        else:
            label_text = f"#{node.id}"
            fg = LColor(1.0, 1.0, 1.0, 1.0)

        tn = TextNode(f"label_{node.id}")
        tn.set_text(label_text)
        tn.set_align(TextNode.ACenter)
        tn.set_text_color(fg)
        tn.set_shadow_color(0, 0, 0, 0.8)
        tn.set_shadow(0.06, 0.06)

        label_np = cell_np.attach_new_node(tn)
        label_np.set_pos(wx, wy, WALL_HEIGHT * 0.55)
        label_np.set_scale(0.5)
        label_np.set_billboard_point_eye()  # always face camera
        label_np.set_light_off()  # ignore scene lighting so text is readable

    def _setup_camera(self) -> None:
        """Position camera at the maze entry for first-person view."""
        self.disable_mouse()

        # Start at entry if available, otherwise first room
        if self.maze.entry is not None:
            self._current_node = self.maze.entry
        elif self.maze.all_rooms:
            self._current_node = self.maze.all_rooms[0]

        if self._current_node is not None:
            wx, wy = _grid_to_world(self._current_node.row, self._current_node.col)
            self.camera.set_pos(wx, wy, WALL_HEIGHT * 0.45)
        else:
            self.camera.set_pos(0, 0, WALL_HEIGHT * 0.45)

        self.camera.set_hpr(0, 0, 0)
        self.heading = 0.0
        self.pitch = 0.0

        # Adjust near/far clip for dungeon-scale rendering
        self.camLens.set_near_far(0.1, 500.0)
        self.camLens.set_fov(75)

        # Hide the default cursor and capture mouse
        props = WindowProperties()
        props.set_cursor_hidden(True)
        self.win.request_properties(props)
        self.center_x = self.win.get_x_size() // 2
        self.center_y = self.win.get_y_size() // 2

        self._overhead = False

    def _setup_controls(self) -> None:
        """Set up WASD movement and mouse look controls."""
        self.key_map: dict[str, bool] = {
            "forward": False,
            "backward": False,
            "left": False,
            "right": False,
            "up": False,
            "down": False,
        }

        self.accept("w", self._set_key, ["forward", True])
        self.accept("w-up", self._set_key, ["forward", False])
        self.accept("s", self._set_key, ["backward", True])
        self.accept("s-up", self._set_key, ["backward", False])
        self.accept("a", self._set_key, ["left", True])
        self.accept("a-up", self._set_key, ["left", False])
        self.accept("d", self._set_key, ["right", True])
        self.accept("d-up", self._set_key, ["right", False])
        self.accept("space", self._set_key, ["up", True])
        self.accept("space-up", self._set_key, ["up", False])
        self.accept("shift", self._set_key, ["down", True])
        self.accept("shift-up", self._set_key, ["down", False])
        self.accept("escape", self._quit)

        # Press 'o' for overhead birds-eye view
        self.accept("o", self._toggle_overhead)

        # IJKM for maze graph traversal
        self.accept("i", self._traverse, [Direction.NORTH])
        self.accept("m", self._traverse, [Direction.SOUTH])
        self.accept("j", self._traverse, [Direction.WEST])
        self.accept("k", self._traverse, [Direction.EAST])

        self.taskMgr.add(self._update_camera, "update_camera")

    def _set_key(self, key: str, value: bool) -> None:
        """Update key state."""
        self.key_map[key] = value

    def _quit(self) -> None:
        """Exit the viewer."""
        self.userExit()

    def _traverse(self, direction: Direction) -> None:
        """Move to the neighboring node in the given direction.

        All doors are treated as open/unlocked.  If there is no connection
        in the requested direction the key press is silently ignored.
        """
        if self._current_node is None:
            return
        neighbor = self._current_node.get_connection(direction)
        if neighbor is None:
            return
        self._current_node = neighbor
        wx, wy = _grid_to_world(neighbor.row, neighbor.col)
        self.camera.set_pos(wx, wy, WALL_HEIGHT * 0.45)
        self.heading = 0.0
        self.pitch = 0.0
        self.camera.set_hpr(0, 0, 0)
        self._update_location_hud()

    def _toggle_overhead(self) -> None:
        """Toggle between first-person and overhead bird's-eye views."""
        self._overhead = not self._overhead
        if self._overhead:
            max_row = len(self.maze.grid) - 1 if self.maze.grid else 0
            max_col = len(self.maze.grid[0]) - 1 if self.maze.grid else 0
            cx = (max_col * CELL_SIZE) / 2.0
            cy = -(max_row * CELL_SIZE) / 2.0
            view_height = max(max_row, max_col) * CELL_SIZE * 1.2
            self.camera.set_pos(cx, cy, max(view_height, 30))
            self.camera.set_hpr(0, -90, 0)
        else:
            # Return to current node (not entry)
            if self._current_node is not None:
                wx, wy = _grid_to_world(
                    self._current_node.row, self._current_node.col
                )
                self.camera.set_pos(wx, wy, WALL_HEIGHT * 0.45)
            else:
                self.camera.set_pos(0, 0, WALL_HEIGHT * 0.45)
            self.heading = 0.0
            self.pitch = 0.0
            self.camera.set_hpr(0, 0, 0)

    def _update_camera(self, task: object) -> int:
        """Update camera position and orientation each frame."""
        dt = ClockObject.get_global_clock().get_dt()

        # Mouse look (only in first-person mode)
        if not self._overhead and self.mouseWatcherNode.has_mouse():
            mx = self.mouseWatcherNode.get_mouse_x()
            my = self.mouseWatcherNode.get_mouse_y()
            self.heading -= mx * self.mouse_sensitivity
            self.pitch += my * self.mouse_sensitivity
            self.pitch = max(-89, min(89, self.pitch))
            self.camera.set_hpr(self.heading, self.pitch, 0)

            # Re-center the mouse
            self.win.move_pointer(0, self.center_x, self.center_y)

        # Movement
        speed = self.movement_speed * dt
        if self._overhead:
            move = LVector3(0, 0, 0)
            if self.key_map["forward"]:
                move += LVector3(0, 1, 0) * speed
            if self.key_map["backward"]:
                move += LVector3(0, -1, 0) * speed
            if self.key_map["right"]:
                move += LVector3(1, 0, 0) * speed
            if self.key_map["left"]:
                move += LVector3(-1, 0, 0) * speed
            if self.key_map["up"]:
                move += LVector3(0, 0, 1) * speed
            if self.key_map["down"]:
                move += LVector3(0, 0, -1) * speed
        else:
            forward = self.camera.get_quat().get_forward()
            right = self.camera.get_quat().get_right()
            up = LVector3(0, 0, 1)

            move = LVector3(0, 0, 0)
            if self.key_map["forward"]:
                move += forward * speed
            if self.key_map["backward"]:
                move -= forward * speed
            if self.key_map["right"]:
                move += right * speed
            if self.key_map["left"]:
                move -= right * speed
            if self.key_map["up"]:
                move += up * speed
            if self.key_map["down"]:
                move -= up * speed

        self.camera.set_pos(self.camera.get_pos() + move)

        from direct.task import Task  # type: ignore[import-untyped]

        return Task.cont

    def _update_location_hud(self) -> None:
        """Update the on-screen text showing the current node."""
        if self._location_text is None or self._current_node is None:
            return
        node = self._current_node
        if isinstance(node, Room):
            loc = f"Room {node.id}: {node.name}"
        elif isinstance(node, Connection):
            loc = f"Corridor {node.id} ({node.ways}-way)"
        else:
            loc = f"Node {node.id}"
        exits = ", ".join(d.value for d in node.connections)
        self._location_text.setText(f"{loc}  |  Exits: {exits}")  # type: ignore[union-attr]

    def _add_hud(self) -> None:
        """Add a simple HUD with maze info and controls."""
        from direct.gui.OnscreenText import OnscreenText  # type: ignore[import-untyped]

        OnscreenText(
            text=f"D&D Maze: {self.maze.name}",
            pos=(0, 0.92),
            scale=0.06,
            fg=(1, 1, 1, 1),
            shadow=(0, 0, 0, 0.8),
            align=TextNode.ACenter,
        )

        # Location display — updated on traversal
        self._location_text = OnscreenText(
            text="",
            pos=(0, 0.82),
            scale=0.05,
            fg=(1, 1, 0.6, 1),
            shadow=(0, 0, 0, 0.8),
            align=TextNode.ACenter,
        )
        self._update_location_hud()

        controls_text = (
            "WASD: Move | Mouse: Look | IJKM: Traverse N/W/E/S"
            " | O: Overhead | ESC: Quit"
        )
        OnscreenText(
            text=controls_text,
            pos=(0, -0.95),
            scale=0.045,
            fg=(1, 1, 1, 0.8),
            shadow=(0, 0, 0, 0.6),
            align=TextNode.ACenter,
        )


def view_maze_3d(maze: Maze) -> None:
    """Launch the Panda3D 3D viewer for the given maze.

    This is a blocking call — the viewer runs until the user closes it.

    Args:
        maze: The maze to visualize.
    """
    app = MazeViewer(maze)
    app.run()
