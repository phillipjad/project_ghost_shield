from ursina import time, window
from ursina import *
from environment import Environment
from GUIdrone import GUIDrone


class Enviroment_Manager:
    instance = None

    def __init__(self):
        window.size = (800, 600)  # Your dimensions here
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
            takeoff_delay=4.0  # Will take off after 2 seconds
        ))

        # Second drone with a 4-second takeoff delay
        self.drones.append(GUIDrone(
            starter_position=(5, 6, 5),
            takeoff_delay=4.0
        ))

        self.drones.append(GUIDrone(
            starter_position=(3, 0, 3),
            takeoff_delay=4.0
        ))

        # Set the active drone in the environment for coordinate display
        self.environment.set_active_drone(self.drones[0])


        self.drones[0].move_to((5, 5, 5))
        self.drones[0].move_to((-5, 8, -5))
        self.drones[0].move_to((1, 5, 1))


    def run(self):
        # Create an update entity that will run every frame
        updater = Entity()

        def update_function():
            # Check for coordinate-based collisions between drones
            for i in range(len(self.drones)):
                for j in range(i+1, len(self.drones)):
                    if self.drones[i].check_collision(self.drones[j]):
                        self.drones[i].handle_collision()
                        self.drones[j].handle_collision()

            # Regular updates
            for drone in self.drones:
                drone.update(time.dt)
            self.environment.update()

        updater.update = update_function

        # Don't forget to actually run the app!
        self.app.run()
