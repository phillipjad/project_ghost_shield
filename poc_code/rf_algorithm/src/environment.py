from ursina import *
from ursina.prefabs.first_person_controller import FirstPersonController
from ursina.prefabs.editor_camera import EditorCamera


class Environment:
    def __init__(self, terrain_image, terrain_texture, terrain_scale=(30, 4, 30)):
        self.terrain_image = terrain_image
        self.terrain_texture = terrain_texture
        self.terrain_scale = terrain_scale
        self.entities = {}
        self.drones = []
        self.drone_controllers = []
        self.camera_mode = 'first_person'  # Default camera mode
        self.active_drone_index = 0  # Index of the currently displayed drone

    def setup(self):
        """Set up the environment with terrain and base entities"""
        # Create terrain
        terrain = Terrain(heightmap=self.terrain_image, skip=4)
        terrain_entity = Entity(
            model=terrain,
            scale=self.terrain_scale,
            texture=self.terrain_texture,
            collider='mesh'
        )
        self.entities['terrain'] = terrain_entity

        # Create safety floor
        floor_size = max(self.terrain_scale[0], self.terrain_scale[2]) * 3
        safety_floor = Entity(
            model='plane',
            scale=(floor_size, 1, floor_size),
            position=(0, -1, 0),
            collider='box',
            visible=False
        )
        self.entities['safety_floor'] = safety_floor

        # Create first person controller (enabled by default)
        self.player = FirstPersonController(position=(0, 10, 0), scale=0.5)
        self.player.gravity = 0.8
        self.player.speed = 5
        self.player.jump_height = 2
        self.entities['player'] = self.player

        # Create editor camera (disabled initially)
        self.editor_camera = EditorCamera(enabled=False, position=(-1, 10, 0))

        # Camera mode indicator
        self.camera_text = Text(text="Camera: First Person (E for Editor Camera)",
                                position=(0, -0.45), origin=(0, 0))

        self.coords_text = Text(
            text="Coords: (0, 0, 0)",
            scale=1.2,
            origin=(-1, -1),
        )

        # Add drone coordinates text display
        self.drone_coords_text = Text(
            text="Drone: (0, 0, 0)",
            scale=1.2,
            position=(0, 0.45),
            origin=(0, 0),
            color=color.yellow
        )

        return self.entities

    def toggle_camera(self):
        """Switch between first person and editor camera"""
        if self.camera_mode == 'first_person':
            # Switch to editor camera
            self.camera_mode = 'editor'
            self.player.enabled = False

            # Set the editor camera position before enabling it
            self.editor_camera.position = Vec3(1, 6, 22)
            self.editor_camera.enabled = True

            # Make the editor camera look at the center of the terrain
            # This needs to happen after enabling the camera
            self.editor_camera.smoothing_helper.look_at(Vec3(0, -2, -50))

            self.camera_text.text = "Camera: Editor Camera (Q for First Person)"
        else:
            # Switch to first person
            self.camera_mode = 'first_person'
            self.editor_camera.enabled = False

            # Reset player state completely before enabling
            self.player.enabled = True
            self.player.mouse_sensitivity = Vec2(40, 40)

            # Make sure mouse control is restored
            mouse.locked = True

            self.camera_text.text = "Camera: First Person (E for Editor Camera)"


    def get_boundary(self):
        """
        Returns the complete 3D boundary limits of the terrain.

        Returns:
            dict: Dictionary with keys 'x', 'y', 'z', each containing a (min, max) tuple
        """
        # Extract terrain dimensions
        width, height, depth = self.terrain_scale

        # Calculate boundary limits
        min_x = -width / 2
        max_x = width / 2
        min_z = -depth / 2
        max_z = depth / 2

        # Set a higher minimum height to prevent drones from being too close to the terrain
        min_y = 3.0  # Increased from 0 to 3.0 units above base ground level
        max_y = height + 2  # Add a bit of extra height for safety

        print(
            f"Terrain boundaries: X: ({min_x}, {max_x}), Y: ({min_y}, {max_y}), Z: ({min_z}, {max_z})")

        return {
            'x': (min_x, max_x),
            'y': (min_y, max_y),
            'z': (min_z, max_z)
        }


    def set_active_drone(self, drone):
        """Set the drone to track and display coordinates for"""
        self.active_drone = drone

    def update(self):
        if self.camera_mode == 'first_person':
            pos = self.player.position
        else:
            pos = self.editor_camera.position

        self.coords_text.text = f"Coords: ({pos.x:.2f}, {pos.y:.2f}, {pos.z:.2f})"

        # Update drone coordinates if we have an active drone
        if hasattr(self, 'active_drone') and self.active_drone and hasattr(self.active_drone, 'drone_entity'):
            drone_pos = self.active_drone.drone_entity.position
            self.drone_coords_text.text = f"Drone: ({drone_pos.x:.2f}, {drone_pos.y:.2f}, {drone_pos.z:.2f})"
