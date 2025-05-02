from multiprocessing import Queue
from typing import cast   # Change this import
from ursina import time, window
from ursina import *
from time import sleep
import json
from environment import Environment
from GUIdrone import GUIDrone


class Enviroment_Manager:
    instance = None

    def __init__(self):
        window.size = (800, 600)
        self.app = Ursina()
        self.environment = None
        self.drones: dict[str, GUIDrone] = {}
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

        for drone_config in self.config["drones"]:
            drone = GUIDrone(
                starter_position=(0, 0, 0),
                drone_id=drone_config["id"]
            )
            self.drones[drone_config["id"]] = drone

    def run(self, movement_queue: Queue, initialize_queue: Queue):
        # Create an update entity that will run every frame
        updater = Entity()

        # RF simulation thread is now started from rf_simulation.py
        # Just call setup to process the positions
        self.setup()

        def update_function():
            # Process any movement commands in the queue
            try:
                while not movement_queue.empty():
                    drone_id, x, y, z = movement_queue.get_nowait()
                    if drone_id in self.drones:
                        print(
                            f"GUI: Moving drone {drone_id} to ({x}, {y}, {z})")
                        self.drones[drone_id].move_to((x, y, z))
            except Exception as e:
                print(f"Error processing movement commands: {e}")

            # Regular updates for all drones
            for drone in self.drones.values():
                drone.update(time.dt)

            # Update the environment
            self.environment.update()

        updater.update = update_function

        initialize_queue.put("done")
        # Don't forget to actually run the app!
        self.app.run()
