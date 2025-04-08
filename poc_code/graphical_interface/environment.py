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
            self.player.enabled = True
            self.editor_camera.enabled = False
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
        min_y = 0
        max_y = height

        return {
            'x': (min_x, max_x),
            'y': (min_y, max_y),
            'z': (min_z, max_z)
        }

    def update(self):
        if self.camera_mode == 'first_person':
            pos = self.player.position
        else:
            pos = self.editor_camera.position

        self.coords_text.text = f"Coords: ({pos.x:.2f}, {pos.y:.2f}, {pos.z:.2f})"
