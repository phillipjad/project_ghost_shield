from ursina import *
from ursina.prefabs.first_person_controller import FirstPersonController
from drone import GUIDrone
import math
class Environment:
    def __init__(self, terrain_image, terrain_texture, terrain_scale=(30, 4, 30)):
        self.terrain_image = terrain_image
        self.terrain_texture = terrain_texture
        self.terrain_scale = terrain_scale
        self.entities = {}
        self.drones = []

    def setup(self):
        """Set up just the environment with nothing in it"""
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

        # Create player
        player = FirstPersonController(position=(0, 10, 0), scale=0.5)
        player.gravity = 0.8
        player.speed = 5
        player.jump_height = 2
        self.entities['player'] = player

        # Position text
        position_text = Text(text="", position=(-0.5, -0.4))

        return self.entities

    def make_drones(self, positions=None, model_path='model/drone.glb', color=color.orange, scale=0.5):
        """
        Create drones at specified positions or in a circle if none are given.
        Ensures drones are placed on the terrain surface.

        Parameters:
        - positions: Array of tuples with (x,z) coordinates (y will be determined by terrain), None for default circle
        - model_path: Path to the drone model
        - color: Color for the drones
        - scale: Scale for the drones
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
                # Store just x,z - we'll determine y with raycasting
                positions.append((x, z))

        # Create drones at each position
        for i, pos in enumerate(positions):
            # Handle both (x,z) and (x,y,z) formats for backward compatibility
            if len(pos) == 2:
                x, z = pos
                # Start raycast high above the terrain to find ground
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
                y = hit_info.world_point.y + 0.5  # Add slight offset to prevent clipping
            else:
                # Fallback if raycast missed the terrain
                y = 0
                print(
                    f"Warning: Raycast missed terrain at position ({x}, {z}). Using y=0.")

            # Create the drone at the proper height
            drone_creator = GUIDrone(
                model_path=model_path,
                color=color,
                starter_position=(x, y, z),
                scale=scale
            )

            drone_entity = drone_creator.create_drone()
            # Add ID to the drone for reference
            drone_entity.id = i
            drones.append(drone_entity)

        self.drones = drones
        self.entities['drones'] = drones
        return drones

    # Method to update physics for all drones
    def update_drones(self):
        for drone in self.drones:
            if hasattr(drone, 'physics') and drone.physics:
                drone.physics.update()

    def move_drone_to(self, drone_id, target_position):
        """
        Move a specific drone to the target position with realistic physics

        Parameters:
        - drone_id: ID of the drone to move
        - target_position: (x, y, z) coordinate to move to

        Returns:
        - True if drone was found and command sent, False otherwise
        """
        if 0 <= drone_id < len(self.drones):
            drone = self.drones[drone_id]
            if hasattr(drone, 'physics') and drone.physics:
                print(f"Moving drone {drone_id} to {target_position}")
                drone.physics.move_to(target_position)
                return True
        else:
            print(f"Error: Drone ID {drone_id} not found")
        return False

    def fly_all_drones_up(self, height=10):
        """
        Command all drones to fly up to the specified height

        Parameters:
        - height: Height to fly up to
        """
        for i, drone in enumerate(self.drones):
            if hasattr(drone, 'physics') and drone.physics:
                # Move up while keeping x,z position
                target = (drone.x, drone.y + height, drone.z)
                drone.physics.move_to(target)
                print(f"Drone {i} flying up to {target}")


# Usage example
if __name__ == '__main__':
    app = Ursina()
    window.title = "3D Environment"
    scene.ambient_light = color.rgba(0.8, 0.8, 0.8, 1)

    # Create just the environment
    env = Environment(
        terrain_image='assets/grass.png',
        terrain_texture='assets/grass.png',
        terrain_scale=(30, 4, 30)
    )

    # Set up the environment
    env.setup()

    # Add drones in default circle pattern
    env.make_drones()

    # Display a countdown text
    countdown_text = Text(
        text="Drones will take off in 5 seconds", position=(0, 0.4), origin=(0, 0))

    # Schedule drones to fly up after 5 seconds
    def start_flying():
        countdown_text.text = "Drones are now flying!"
        env.fly_all_drones_up(height=10)
        invoke(lambda: setattr(countdown_text, 'enabled', False), delay=3)

    invoke(start_flying, delay=5)

    def update():
        env.update_drones()

    app.run()
