from ursina import *
from ursina.prefabs.first_person_controller import FirstPersonController
from ursina.prefabs.editor_camera import EditorCamera
from drone import GUIDrone
import math


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
            position=(0, -2, 0),
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

        # Position text
        position_text = Text(text="", position=(-0.5, -0.4))

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

    def make_drones(self, positions=None, model_path='model/drone.glb', color=color.orange, scale=0.5):
        """
        Create drones at specified positions or in a circle if none are given.
        Ensures drones are placed on the terrain surface.
        """
        drones = []

        # If no positions provided, create a circle on the ground
        if positions is None:
            drone_count = 5  # Default count
            radius = min(self.terrain_scale[0], self.terrain_scale[2]) / 4

            positions = []
            for i in range(drone_count):
                angle = (i / drone_count) * 2 * math.pi
                x = math.cos(angle) * radius
                z = math.sin(angle) * radius
                positions.append((x, z))

        # Create drones at each position
        for i, pos in enumerate(positions):
            # Handle both (x,z) and (x,y,z) formats
            if len(pos) == 2:
                x, z = pos
                start_height = self.terrain_scale[1] * 2
                ray_origin = Vec3(x, start_height, z)
            else:
                x, _, z = pos
                start_height = self.terrain_scale[1] * 2
                ray_origin = Vec3(x, start_height, z)

            # Cast ray downward to find terrain height at this position
            hit_info = raycast(
                origin=ray_origin,
                direction=Vec3(0, -1, 0),
                distance=start_height * 2,
                traverse_target=self.entities['terrain']
            )

            # Set the drone position based on terrain height
            if hit_info.hit:
                y = hit_info.world_point.y + 0.5  # Add offset to prevent clipping
            else:
                y = 0
                print(
                    f"Warning: Raycast missed terrain at position ({x}, {z}). Using y=0.")

            # Create the drone at the proper height
            drone_controller = GUIDrone(
                model_path=model_path,
                color=color,
                starter_position=(x, y, z),
                scale=scale
            )

            drone_entity = drone_controller.create_drone()
            drone_entity.id = i  # Add ID for reference

            drones.append(drone_entity)
            self.drone_controllers.append(drone_controller)

        self.drones = drones
        self.entities['drones'] = drones
        return drones

    def update(self):
        """Update all entities in the environment"""
        dt = time.dt

        # Update all drones
        for controller in self.drone_controllers:
            controller.update(dt)

        # Here you would update other physics entities in the environment

    def move_drone(self, drone_id, target_position):
        """
        Move a specific drone to the target position

        Parameters:
        - drone_id: ID of the drone to move
        - target_position: (x,y,z) or (x,z) coordinates

        Returns:
        - True if command was sent successfully, False otherwise
        """
        if 0 <= drone_id < len(self.drone_controllers):
            controller = self.drone_controllers[drone_id]
            print(f"Moving drone {drone_id} to {target_position}")
            return controller.move_to(target_position)
        else:
            print(f"Error: Drone ID {drone_id} not found")
            return False

    def get_drone_position(self, drone_id):
        """Get the current position of a drone"""
        if 0 <= drone_id < len(self.drones):
            return self.drones[drone_id].position
        return None


# Usage example
if __name__ == '__main__':
    app = Ursina()
    window.title = "3D Environment"
    scene.ambient_light = color.rgba(0.8, 0.8, 0.8, 1)

    # Create environment
    env = Environment(
        terrain_image='assets/grass.png',
        terrain_texture='assets/grass.png',
        terrain_scale=(30, 4, 30)
    )

    # Set up environment
    env.setup()

    # Add drones in default circle pattern
    env.make_drones()

    # Display a countdown text
    countdown_text = Text(
        text="Drones will move in 5 seconds", position=(0, 0.4), origin=(0, 0))

    # Global variable for figure-8 animation
    figure_8_time = 0

    # Define input handler for camera switching
    def input(key):
        if key == 'q':  # Switch to first-person camera
            if env.camera_mode == 'editor':  # Only switch if we're not already in this mode
                env.toggle_camera()
        elif key == 'e':  # Switch to editor camera
            if env.camera_mode == 'first_person':  # Only switch if we're not already in this mode
                env.toggle_camera()

    # Function to continuously move drones in a figure-8 pattern
    def update_figure_8_positions():
        global figure_8_time
        figure_8_time += 0.02  # Time increment for smooth movement

        # Parameters for the figure-8
        width = 15   # Width of the figure-8
        height = 8   # Height of the figure-8
        altitude = 12  # Flying height

        # Move each drone along the figure-8 path with offset
        for i in range(len(env.drones)):
            # Offset each drone in time to distribute them along the path
            t = figure_8_time + (i / len(env.drones)) * 2 * math.pi

            # Figure-8 parametric equations
            x = width * math.sin(t)
            z = height * math.sin(2 * t)  # Creates the figure-8 shape
            y = altitude

            # Move the drone
            env.move_drone(i, (x, y, z))

        # Continue the movement
        invoke(update_figure_8_positions, delay=0.1)

    # Function to start figure-8 formation
    def start_figure_8_formation():
        countdown_text.text = "Drones moving in figure-8 formation!"
        update_figure_8_positions()

    # Function to move drones after delay
    def move_drones_after_delay():
        countdown_text.text = "Drones are now moving!"

        # Move each drone to a different position in a circle
        for i in range(len(env.drones)):
            # Calculate a target position
            angle = (i / len(env.drones)) * 2 * math.pi
            x = math.cos(angle) * 10  # Larger radius
            z = math.sin(angle) * 10
            y = 8  # Height above ground

            # Move the drone
            env.move_drone(i, (x, y, z))

        # Hide countdown text after 3 seconds
        invoke(lambda: setattr(countdown_text, 'enabled', False), delay=3)

        # Schedule figure-8 formation after circle formation
        invoke(start_figure_8_formation, delay=10)

    # Schedule movement
    invoke(move_drones_after_delay, delay=5)

    # Update function
    def update():
        env.update()

    app.run()
