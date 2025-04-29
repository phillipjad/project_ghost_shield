from ursina import time
from ursina import *
from environment import Environment
from GUIdrone import GUIDrone


class Enviroment_Manager:
    instance = None

    def __init__(self):
        self.app = Ursina()
        self.environment = None
        self.drones = []
        Enviroment_Manager.instance = self

    def setup(self):

        # Set up the environment
        self.environment = Environment(
            terrain_image='assets/grass.png',
            terrain_texture='assets/grass.png',
            terrain_scale=(30, 4, 30)
        )

        self.environment.setup()

        # Create the first drone
        drone1 = GUIDrone(
            starter_position=(1, 5, 1),
        )
        self.drones.append(drone1)

        # Create a second drone with different color
        drone2 = GUIDrone(
            starter_position=(-1, 5, -1),
            color=color.rgb(200, 50, 50)  # Red color to distinguish it
        )
        self.drones.append(drone2)

        # IMPORTANT: Add drones to the class tracking list for collision detection
        GUIDrone.all_drones = self.drones

        # Set the active drone in the environment for coordinate display
        self.environment.set_active_drone(self.drones[0])

        # Set up drone movements with delays to create a guaranteed collision
        # Both drones will move to the exact same position (0, 7, 0)

        # First drone movement path
        # This is where collision will happen
        self.drones[0].move_to((0, 7, 0), delay=4)

        # Second drone movement path (will meet first drone at the collision point)
        self.drones[1].move_to((-5, 5, -5), delay=3)  # First move away
        # Then move to collision point
        self.drones[1].move_to((0, 7, 0), delay=6)

        print("boundary:", self.environment.get_boundary())

    def run(self):
        # Create an update entity that will run every frame
        updater = Entity()

        def update_function():
            for drone in self.drones:
                drone.update(time.dt)
            self.environment.update()
        updater.update = update_function

        # Don't forget to actually run the app!
        self.app.run()
