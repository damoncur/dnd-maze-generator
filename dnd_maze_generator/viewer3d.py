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
    DirectionalLight,
    LColor,
    LVector3,
    NodePath,
    PointLight,
    TextNode,
    WindowProperties,
)

from .models import Direction, DoorType, Maze, MazeNode, Room

# Dimensions for each grid cell in 3D space
CELL_SIZE = 6.0
WALL_HEIGHT = 4.0
WALL_THICKNESS = 0.15
DOOR_THICKNESS = 0.1

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
    DoorType.HIDDEN: LColor(0.35, 0.30, 0.25, 0.6),  # semi-transparent
}

# Direction offsets for wall placement
_DIR_OFFSETS: dict[Direction, tuple[float, float]] = {
    Direction.NORTH: (0.0, 1.0),
    Direction.SOUTH: (0.0, -1.0),
    Direction.EAST: (1.0, 0.0),
    Direction.WEST: (-1.0, 0.0),
}


def _make_card(name: str, width: float, height: float, color: LColor) -> NodePath:
    """Create a colored rectangular card (quad)."""
    cm = CardMaker(name)
    cm.set_frame(-width / 2, width / 2, -height / 2, height / 2)
    cm.set_color(color)
    node = cm.generate()
    return NodePath(node)


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

    def _setup_lighting(self) -> None:
        """Set up ambient and directional lighting."""
        # Ambient light for base visibility
        ambient = AmbientLight("ambient")
        ambient.set_color(LColor(0.3, 0.3, 0.3, 1.0))
        ambient_np = self.render.attach_new_node(ambient)
        self.render.set_light(ambient_np)

        # Directional light from above
        sun = DirectionalLight("sun")
        sun.set_color(LColor(0.7, 0.65, 0.6, 1.0))
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
        cell_np.set_pos(wx, wy, 0)

        is_room = isinstance(node, Room)
        floor_color = COLOR_ROOM_FLOOR if is_room else COLOR_CORRIDOR_FLOOR

        # Floor
        floor = _make_card(f"floor_{node.id}", CELL_SIZE, CELL_SIZE, floor_color)
        floor.reparent_to(cell_np)
        floor.set_p(-90)  # lay flat
        floor.set_pos(0, 0, 0)

        # Ceiling
        ceiling = _make_card(f"ceiling_{node.id}", CELL_SIZE, CELL_SIZE, COLOR_CEILING)
        ceiling.reparent_to(cell_np)
        ceiling.set_p(90)  # lay flat facing down
        ceiling.set_pos(0, 0, WALL_HEIGHT)

        # Walls on sides without exits
        for direction in [Direction.NORTH, Direction.SOUTH, Direction.EAST, Direction.WEST]:
            if node.has_connection(direction):
                # There's an exit here — check for doors
                if is_room:
                    assert isinstance(node, Room)
                    door = node.get_door(direction)
                    if door is not None:
                        self._build_door(cell_np, direction, door.door_type)
                continue
            self._build_wall(cell_np, direction)

        # Add a point light inside rooms for atmosphere
        if is_room:
            plight = PointLight(f"light_{node.id}")
            plight.set_color(LColor(0.8, 0.7, 0.5, 1.0))
            plight.set_attenuation((1.0, 0.05, 0.01))
            plight_np = cell_np.attach_new_node(plight)
            plight_np.set_pos(0, 0, WALL_HEIGHT * 0.8)
            self.render.set_light(plight_np)

    def _build_wall(self, cell_np: NodePath, direction: Direction) -> None:
        """Place a wall on the given side of a cell."""
        wall = _make_card(f"wall_{direction.value}", CELL_SIZE, WALL_HEIGHT, COLOR_WALL)
        wall.reparent_to(cell_np)
        wall.set_two_sided(True)

        half = CELL_SIZE / 2.0
        if direction == Direction.NORTH:
            wall.set_pos(0, half, WALL_HEIGHT / 2)
            wall.set_h(0)
        elif direction == Direction.SOUTH:
            wall.set_pos(0, -half, WALL_HEIGHT / 2)
            wall.set_h(180)
        elif direction == Direction.EAST:
            wall.set_pos(half, 0, WALL_HEIGHT / 2)
            wall.set_h(-90)
        elif direction == Direction.WEST:
            wall.set_pos(-half, 0, WALL_HEIGHT / 2)
            wall.set_h(90)

    def _build_door(self, cell_np: NodePath, direction: Direction, door_type: DoorType) -> None:
        """Place a door on the given side of a cell."""
        color = DOOR_COLORS.get(door_type, DOOR_COLORS[DoorType.WOODEN])
        # Door is slightly smaller than the full opening
        door_width = CELL_SIZE * 0.7
        door_height = WALL_HEIGHT * 0.8
        door = _make_card(f"door_{direction.value}", door_width, door_height, color)
        door.reparent_to(cell_np)
        door.set_two_sided(True)

        half = CELL_SIZE / 2.0
        if direction == Direction.NORTH:
            door.set_pos(0, half, door_height / 2)
            door.set_h(0)
        elif direction == Direction.SOUTH:
            door.set_pos(0, -half, door_height / 2)
            door.set_h(180)
        elif direction == Direction.EAST:
            door.set_pos(half, 0, door_height / 2)
            door.set_h(-90)
        elif direction == Direction.WEST:
            door.set_pos(-half, 0, door_height / 2)
            door.set_h(90)

        # Add lintel (wall above door)
        lintel_height = WALL_HEIGHT - door_height
        if lintel_height > 0.1:
            lintel = _make_card(
                f"lintel_{direction.value}", CELL_SIZE, lintel_height, COLOR_WALL
            )
            lintel.reparent_to(cell_np)
            lintel.set_two_sided(True)
            lintel_z = door_height + lintel_height / 2
            if direction == Direction.NORTH:
                lintel.set_pos(0, half, lintel_z)
                lintel.set_h(0)
            elif direction == Direction.SOUTH:
                lintel.set_pos(0, -half, lintel_z)
                lintel.set_h(180)
            elif direction == Direction.EAST:
                lintel.set_pos(half, 0, lintel_z)
                lintel.set_h(-90)
            elif direction == Direction.WEST:
                lintel.set_pos(-half, 0, lintel_z)
                lintel.set_h(90)

    def _setup_camera(self) -> None:
        """Position camera at the maze entry for first-person view."""
        self.disable_mouse()

        # Start at entry if available, otherwise first room
        start_node: Optional[MazeNode] = None
        if self.maze.entry is not None:
            start_node = self.maze.entry
        elif self.maze.all_rooms:
            start_node = self.maze.all_rooms[0]

        if start_node is not None:
            wx, wy = _grid_to_world(start_node.row, start_node.col)
            self.camera.set_pos(wx, wy, WALL_HEIGHT * 0.5)
        else:
            self.camera.set_pos(0, 0, WALL_HEIGHT * 0.5)

        self.camera.set_hpr(0, 0, 0)
        self.heading = 0.0
        self.pitch = 0.0

        # Hide the default cursor and capture mouse
        props = WindowProperties()
        props.set_cursor_hidden(True)
        self.win.request_properties(props)
        self.center_x = self.win.get_x_size() // 2
        self.center_y = self.win.get_y_size() // 2

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

        self.taskMgr.add(self._update_camera, "update_camera")

    def _set_key(self, key: str, value: bool) -> None:
        """Update key state."""
        self.key_map[key] = value

    def _quit(self) -> None:
        """Exit the viewer."""
        self.userExit()

    def _update_camera(self, task: object) -> int:
        """Update camera position and orientation each frame."""
        dt = globalClock.get_dt()  # type: ignore[name-defined]  # noqa: F821

        # Mouse look
        if self.mouseWatcherNode.has_mouse():
            mx = self.mouseWatcherNode.get_mouse_x()
            my = self.mouseWatcherNode.get_mouse_y()
            self.heading -= mx * self.mouse_sensitivity * 100 * dt
            self.pitch += my * self.mouse_sensitivity * 100 * dt
            self.pitch = max(-89, min(89, self.pitch))
            self.camera.set_hpr(self.heading, self.pitch, 0)

            # Re-center the mouse
            self.win.move_pointer(0, self.center_x, self.center_y)

        # Movement
        speed = self.movement_speed * dt
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

        controls_text = "WASD: Move | Mouse: Look | Space/Shift: Up/Down | ESC: Quit"
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
