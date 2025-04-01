from ursina import *
from environment import Environment


class Enviroment_Manager:
    instance = None

    def __init__(self):
        self.app = Ursina()
        self.environment = None
        Enviroment_Manager.instance = self

    def setup(self):
        self.environment = Environment(
            terrain_image='assets/grass.png',
            terrain_texture='assets/grass.png',
            terrain_scale=(30, 4, 30)
        )
        self.environment.setup()

    def run(self):
        self.app.run()
