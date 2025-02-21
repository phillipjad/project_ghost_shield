import random

from drone import Drone
from utils.graph_wrapper import DroneGraph
from rf_simulation import mark_drone_moved


class Field:
    """2 or 3 dimensional field. Used to give space for drone simulation"""

    def __init__(
        self, x_size: float, y_size: float, z_size: float | None, drones: list[Drone]
    ) -> None:
        self.x_size = x_size
        self.y_size = y_size
        self.z_size = z_size
        self.drones = drones

    def randomly_place_drones(self) -> None:
        for drone in self.drones:
            drone.move_x(random.randint(0, int(self.x_size - 1)))
            drone.move_y(random.randint(0, int(self.y_size - 1)))
            if self.z_size:
                drone.move_z(random.randint(0, int(self.z_size - 1)))

    def drones_are_equidistant(self) -> bool:
        drones_equidistant = True
        prev_distance = -1
        for drone in self.drones:
            for other_drone in self.drones:
                if drone is not other_drone:
                    if prev_distance == drone.calc_distance_between_drones(other_drone):
                        continue
                    elif prev_distance == -1:
                        prev_distance = drone.calc_distance_between_drones(other_drone)
                        continue
                    else:
                        drones_equidistant = False
                        break
            break
        return drones_equidistant

    def space_drones(self, drone_graph: DroneGraph = None) -> None:
        for drone in self.drones:
            for other_drone in self.drones:
                if drone is not other_drone:
                    pass  # TODO
        # Only mark the drone as moved if it has actually moved
        mark_drone_moved(drone)

    def __str__(self) -> str:
        return f"""
            Field with dimensions: [{self.x_size}, {self.y_size}, {self.z_size}]
            Drones: {str.join(chr(10), [str(d) for d in self.drones])}
        """
