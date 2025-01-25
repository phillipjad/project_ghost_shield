from drone import Drone
import random
import copy

class Field:
    """2 or 3 dimensional field. Used to give space for drone simulation
    """
    def __init__(self, x_size: float, y_size: float, z_size: float | None, drones: list[Drone]) -> None:
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
        num_drones = len(self.drones)
        cloned_drones = copy.deepcopy(self.drones)
        for _ in range(num_drones):
            prev_distance = -1
            temp_drone = cloned_drones.pop()
            for drone in cloned_drones:
                if prev_distance == -1:
                    prev_distance = temp_drone.calc_distance_between_drones(drone)
                    continue
                if prev_distance == temp_drone.calc_distance_between_drones(drone):
                    continue
                else:
                    drones_equidistant = False
                    break
            if drones_equidistant:
                continue
            else:
                break
        return drones_equidistant



    def __str__(self) -> str:
        return f"""
            Field with dimensions: [{self.x_size}, {self.y_size}, {self.z_size}]
            Drones: {str.join(chr(10), [str(d) for d in self.drones])}
        """