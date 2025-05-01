from threading import Thread
from ursina import time, window
from ursina import *
import json
import random
from environment import Environment
from GUIdrone import GUIDrone
from rf_simulation import main as rf_main_func
from queue import Queue

q = Queue()

class Enviroment_Manager:
    instance = None

    def __init__(self):
        window.size = (800, 600)
        self.app = Ursina()
        self.environment = None
        self.drones = []
        Enviroment_Manager.instance = self

        # Load config
        with open("config.json", "r") as f:
            self.config = json.load(f)

    def generate_unique_positions(self, num_positions, bounds):
        """
        Randomly place drones within the environment bounds, similar to field.py's approach.

        :param num_positions: Number of positions to generate
        :param bounds: A dictionary with keys 'x', 'y', 'z' containing (min, max) tuples
        :return: A list of unique (x, y, z) tuples
        """
        positions = []

        for _ in range(num_positions):
            # Use the full range of the environment
            x = random.uniform(bounds['x'][0], bounds['x'][1])
            # Ensure y is positive
            y = random.uniform(max(0, bounds['y'][0]), bounds['y'][1])
            z = random.uniform(bounds['z'][0], bounds['z'][1])

            # Round to avoid floating-point precision issues
            position = (round(x, 2), round(y, 2), round(z, 2))
            positions.append(position)

        return positions

    def setup(self):
        env_cfg = self.config["environment"]
        dims = env_cfg["dimensions"]
        assets = env_cfg["assets"]

        # Set up the environment
        self.environment = Environment(
            terrain_image=assets["terrain_image"],
            terrain_texture=assets["terrain_texture"],
            terrain_scale=(dims["x"], dims["y"], dims["z"])  # Adjust as needed
        )

        self.environment.setup()

        # Generate unique positions for drones
        unique_positions = self.generate_unique_positions(
            len(self.config["drones"]), self.environment.get_boundary())

        print("Unique positions for drones:", unique_positions)
        for i in range(len(self.config["drones"])):
            self.drones.append(GUIDrone(
                starter_position=unique_positions[i],
                takeoff_delay=4
            ))
        q.put(self.drones)

    def run(self):
        # Create an update entity that will run every frame
        updater = Entity()
        Thread(
            target=rf_main_func,
            args=(q,),
            daemon=True
        ).start()

        def update_function():
            # Regular updates for all drones
            for drone in self.drones:
                drone.update(time.dt)

            # Update the environment
            self.environment.update()

        updater.update = update_function

        # Don't forget to actually run the app!
        self.app.run()
