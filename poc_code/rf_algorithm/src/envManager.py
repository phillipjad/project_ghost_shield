from multiprocessing import Queue   # Change this import
from ursina import time, window
from ursina import *
from time import sleep
import json
from environment import Environment
from GUIdrone import GUIDrone
from rf_simulation import main as rf_main_func

positions_queue = Queue()  # RF -> GUI
drones_queue = Queue()     # GUI -> RF


class Enviroment_Manager:
    instance = None

    def __init__(self):
        window.size = (800, 600)
        self.app = Ursina()
        self.environment = None
        self.drones = []
        Enviroment_Manager.instance = self

        # Load config
        with open("config/system_config.json", "r") as f:
            self.config = json.load(f)

    def setup(self):
        env_cfg = self.config["environment"]
        dims = env_cfg["dimensions"]
        assets = env_cfg["assets"]

        # Set up the environment
        self.environment = Environment(
            terrain_image=assets["terrain_image"],
            terrain_texture=assets["terrain_texture"],
            terrain_scale=(dims["x"], dims["y"], dims["z"])
        )
        self.environment.setup()

        num_drones = len(self.config["drones"])
        received_positions = {}

        for _ in range(num_drones):
            idx, x, y, z = positions_queue.get()
            print("Received position for idx", idx, ":", (x, y, z))
            received_positions[idx] = (x, y, z)

        # Sort by index to match config
        for idx in sorted(received_positions.keys()):
            drone_cfg = self.config["drones"][idx]
            starter_position = received_positions[idx]

            drone = GUIDrone(
                starter_position=starter_position,
                drone_id=drone_cfg["id"]
            )
            self.drones.append(drone)

        drones_queue.put(self.drones)

    def run(self):
        # Create an update entity that will run every frame
        updater = Entity()

        # RF simulation thread is now started from rf_simulation.py
        # Just call setup to process the positions
        self.setup()

        def update_function():
            # Regular updates for all drones
            for drone in self.drones:
                drone.update(time.dt)

            # Update the environment
            self.environment.update()

        updater.update = update_function

        # Don't forget to actually run the app!
        self.app.run()
