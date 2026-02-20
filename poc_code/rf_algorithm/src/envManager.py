from queue import Queue
from threading import Thread
import multiprocessing as mp
from typing import cast   # Change, his import
from ursina import time, window
from ursina import *
from time import sleep
import json
from environment import Environment
from GUIdrone import GUIDrone
from rf_simulation import main as rf_algorithm_exec


class Enviroment_Manager:
    instance = None

    def __init__(self):
        window.size = (1500, 1000)
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

    def run(self, PROCESS_LIST: list[mp.Process]):
        # Create an update entity that will run every frame
        updater = Entity()

        # Just call setup to process the positions
        self.setup()

        rf_thread = Thread (
            target=rf_algorithm_exec,
            args=(False, self.drones, PROCESS_LIST),
            daemon=True,
        )
        rf_thread.start()

        def update_function():
            # Regular updates for all drones
            for drone in self.drones.values():
                drone.update(time.dt)

            # Update the environment
            self.environment.update()

        updater.update = update_function

        # Don't forget to actually run the app!
        self.app.run()
