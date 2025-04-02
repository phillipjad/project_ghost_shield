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
        self.editor_camera = EditorCamera(enabled=False)

        # Camera mode indicator
        self.camera_text = Text(text="Camera: First Person (E for Editor Camera)",
                                position=(0, -0.45), origin=(0, 0))

        return self.entities

    def toggle_camera(self):
        """Switch between first person and editor camera"""
        if self.camera_mode == 'first_person':
            # Switch to editor camera
            self.camera_mode = 'editor'
            self.player.enabled = False
            self.editor_camera.enabled = True
            self.camera_text.text = "Camera: Editor Camera (Q for First Person)"
        else:
            # Switch to first person
            self.camera_mode = 'first_person'
            self.player.enabled = True
            self.editor_camera.enabled = False
            self.camera_text.text = "Camera: First Person (E for Editor Camera)"

    def get_boundary(self):
        """
        Returns 4 coordinates (x, y) that define the boundary of the terrain
        in the first quadrant (positive values only).

        Note: These are actually (x, z) coordinates on the ground plane,
        but returned as (x, y) pairs as requested.
        """
        # Get the scale of the terrain
        x_scale = self.terrain_scale[0]
        z_scale = self.terrain_scale[2]

        # Calculate the maximum positive extent of the terrain
        # Assuming the terrain is centered at the origin
        max_x = x_scale / 2
        max_z = z_scale / 2

        # Define the 4 corners of the first quadrant boundary
        # Starting from the origin and going clockwise
        boundary_coords = [
            (0, 0),         # Origin
            (max_x, 0),     # Maximum x, minimum z
            (max_x, max_z),  # Maximum x, maximum z
            (0, max_z)      # Minimum x, maximum z
        ]

        return boundary_coords
    
    def get_height(self):
        """
        Returns the height of the terrain.
        """
        return self.terrain_scale[1]
