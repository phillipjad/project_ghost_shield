import random
from typing import cast

from drone import Drone
from utils.distance_obj import Distance
from utils.graph_wrapper import DroneGraph
from utils.vector import Vector


class Field:
    """2 or 3 dimensional field. Used to give space for drone simulation"""

    def __init__(self, x_size: float, y_size: float, z_size: float | None, drones: list[Drone]) -> None:
        self.x_size = x_size
        self.y_size = y_size
        self.z_size = z_size
        self.drones = drones

    def randomly_place_drones(self) -> None:
        """Randomly places the drones in the field.
        """
        for drone in self.drones:
            drone.move_x(random.randint(0, int(self.x_size - 1)))
            drone.move_y(random.randint(0, int(self.y_size - 1)))
            if self.z_size:
                drone.move_z(random.randint(0, int(self.z_size - 1)))

    def drones_are_equidistant(self, drone_graph: DroneGraph, controller_location: Vector) -> bool:
        distances: list[Distance] = []
        for i in drone_graph.edges():
            i = cast(Distance, i)
            distance = i.distance_between_vectors_using_abs(controller_location)
            distances.append(distance)

        return distances.count(distances[0]) == len(distances)

    def __str__(self) -> str:
        """Returns a string representation of the field.
        This includes the dimensions of the field and the drones in the field.
        """
        return f"""
            Field with dimensions: [{self.x_size}, {self.y_size}, {self.z_size}]
            Drones: {str.join(chr(10), [str(d) for d in self.drones])}
        """
