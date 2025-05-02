from threading import Thread
from ursina import time, window
from ursina import *
from time import sleep
import json
from environment import Environment
from GUIdrone import GUIDrone
from rf_simulation import main as rf_main_func
from queue import Queue

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
        with open("config.json", "r") as f:
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

        # === Get positions from simulation ===
        print("Getting positions from simulation")
        drone_positions = positions_queue.get()
        print("Received positions:", drone_positions)

        for i, pos in enumerate(drone_positions):
            self.drones.append(GUIDrone(
                starter_position=pos,
            ))


        # Signal GUI is ready and send drones back
        print("Putting GUI drones in queue")
        drones_queue.put(self.drones)


    def run(self):
        # Create an update entity that will run every frame
        updater = Entity()
        
        # Start the RF simulation thread with the new queues and events
        Thread(
            target=rf_main_func,
            args=(positions_queue, drones_queue,),
            daemon=True
        ).start()
        
        # Call setup to process the positions
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