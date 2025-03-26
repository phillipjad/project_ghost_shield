from copy import copy

from utils.vector import Vector


class Controller:
    def __init__(self, x: float, y: float, z: float) -> None:
        self.location = Vector(x, y, z)

    def get_location(self) -> Vector:
        return copy(self.location)
