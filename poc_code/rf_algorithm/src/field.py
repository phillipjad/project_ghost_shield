import random

from drone import Drone
from rf_simulation import mark_drone_moved
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
        repulsion_strength = 2.0  # how strong the repulsion is
        damping = 0.15  # how much of the force to apply
        min_distance = 1.0 # minimum distance between drones 

        for out_id in drone_graph.node_indices():
            force_vector = [0.0, 0.0, 0.0] #there is no force initially

            for in_id in drone_graph.node_indices(): 
                if out_id == in_id: # skip if it is the same drone
                    continue

                edge_data: Distance = drone_graph.get_edge_data(out_id, in_id)
                distance_vector = edge_data.get_vector() 
                if edge_data.get_last_to_write() != in_id:
                    distance_vector = (-1 * distance_vector[0], -1 * distance_vector[1], -1 * distance_vector[2])

                # calculate the Euclidean distance between the two drones
                distance = max(min_distance, math.sqrt(distance_vector[0]**2 + distance_vector[1]**2 + distance_vector[2]**2))

                force = repulsion_strength / (distance ** 2) 
                # calculate the force between the drones the formula is f = repulsion_strength / distance^2
                # the closer the 2 drones the stronger the force

                force_vector[0] += (distance_vector[0] / distance) * force # calculate the force for x axis
                force_vector[1] += (distance_vector[1] / distance) * force # calculate the force for y axis
                force_vector[2] += (distance_vector[2] / distance) * force # calculate the force for z axis
            new_x = drone_graph.get_node_data(out_id).get_x() + force_vector[0] * damping # calculate the new x coordinate
            new_y = drone_graph.get_node_data(out_id).get_y() + force_vector[1] * damping # calculate the new y coordinate
            new_z = drone_graph.get_node_data(out_id).get_z() + force_vector[2] * damping # calculate the new z coordinate

            drone_graph.get_node_data(out_id).set_x(max(0, min(self.x_size, new_x)))
            drone_graph.get_node_data(out_id).set_y(max(0, min(self.y_size, new_y)))
            if self.z_size:
                drone_graph.get_node_data(out_id).set_z(max(0, min(self.z_size, new_z)))
            damping += 0.05
        # Only mark the drone as moved if it has actually moved
        mark_drone_moved(drone)

    def __str__(self) -> str:
        return f"""
            Field with dimensions: [{self.x_size}, {self.y_size}, {self.z_size}]
            Drones: {str.join(chr(10), [str(d) for d in self.drones])}
        """
