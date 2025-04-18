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

        self.drones.append(GUIDrone(
            starter_position=(1, 5, 1),
        ))

        # Add delay to allow for initial takeoff
        # Move after 4 seconds (extra time to see initial takeoff)
        invoke(lambda: self.drones[0].move_to((5, 5, 5)), delay=4)
        # Move again after 7 seconds
        invoke(lambda: self.drones[0].move_to((-5, 8, -5)), delay=7)
        # And return to start after 10 seconds
        invoke(lambda: self.drones[0].move_to((1, 5, 1)), delay=10)

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
