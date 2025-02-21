import random

from drone import Drone
from utils.graph_wrapper import DroneGraph
import math


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
        distances = []
        drones = self.drones
        for i in range(len(drones)):
            for j in range(i+1, len(drones)):
                distances.append(
                    drones[i].calc_distance_between_drones(drones[j]))

        if not distances:
            return True

        avg = sum(distances)/len(distances)
        return all(math.isclose(d, avg, rel_tol=0.05) for d in distances)

    def space_drones(self, drone_graph: DroneGraph = None) -> None:
        REPULSION_STRENGTH = 2.0  # how strong the repulsion is
        DAMPING = 0.3  # how much of the force to apply
        MIN_DISTANCE = 1.0 # minimum distance between drones 

        for drone in self.drones:
            force_vector = [0.0, 0.0, 0.0] #there is no force initially

            for other_drone in self.drones: 
                if drone is other_drone: # skip if it is the same drone
                    continue

                dx = drone.get_x() - other_drone.get_x() # calculate the distance between the drones for x axis
                dy = drone.get_y() - other_drone.get_y() # calculate the distance between the drones for y axis
                dz = drone.get_z() - other_drone.get_z() # calculate the distance between the drones for z axis

                # calculate the Euclidean distance between the two drones
                distance = max(MIN_DISTANCE, math.sqrt(dx**2 + dy**2 + dz**2))

                force = REPULSION_STRENGTH / (distance ** 2) 
                # calculate the force between the drones the formula is f = repulsion_strength / distance^2
                # the closer the 2 drones the stronger the force

                force_vector[0] += (dx / distance) * force # calculate the force for x axis
                force_vector[1] += (dy / distance) * force # calculate the force for y axis
                force_vector[2] += (dz / distance) * force # calculate the force for z axis
            new_x = drone.get_x() + force_vector[0] * DAMPING # calculate the new x coordinate
            new_y = drone.get_y() + force_vector[1] * DAMPING # calculate the new y coordinate
            new_z = drone.get_z() + force_vector[2] * DAMPING # calculate the new z coordinate

            drone.x = max(0, min(self.x_size, new_x))
            drone.y = max(0, min(self.y_size, new_y))
            if self.z_size:
                drone.z = max(0, min(self.z_size, new_z))

    def __str__(self) -> str:
        return f"""
            Field with dimensions: [{self.x_size}, {self.y_size}, {self.z_size}]
            Drones: {str.join(chr(10), [str(d) for d in self.drones])}
        """
