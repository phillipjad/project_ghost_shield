import math
import random
from typing import cast

from drone import Drone
from utils.vector import Vector
from utils.distance_obj import Distance
from utils.graph_wrapper import DroneGraph


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

    def drones_are_equidistant(self, drone_graph: DroneGraph, controller_location: Vector) -> bool:
        distances: list[Distance] = []
        for i in drone_graph.edges():
            i = cast(Distance, i)
            distance = i.distance_between_vectors_using_abs(controller_location)
            distances.append(distance)

        return distances.count(distances[0]) == len(distances)

    def space_drones(self, drone_graph: DroneGraph, update_edge_function: callable) -> None:
        repulsion_strength = 2.0  # how strong the repulsion is
        damping = 0.15  # how much of the force to apply
        min_distance = 1.0  # minimum distance between drones

        for out_id in drone_graph.node_indices():
            force_vector = Vector(0.0, 0.0, 0.0)  # there is no force initially

            for in_id in drone_graph.node_indices():
                if out_id == in_id:  # skip if it is the same drone
                    continue

                edge_data: Distance = drone_graph.get_edge_data(out_id, in_id)
                distance_vector = edge_data.get_vector()
                if edge_data.get_last_to_write() != out_id:
                    distance_vector = distance_vector.as_negated() 
                    

                curr_force_vector = distance_vector.calculate_force(min_distance, repulsion_strength)
                force_vector.mutating_vector_sum(curr_force_vector)
            force_vector_components = force_vector.get_internals_as_tuple()
            new_x = (
                drone_graph.get_node_data(out_id).get_x() + force_vector_components[0] * damping
            )  # calculate the new x coordinate
            new_y = (
                drone_graph.get_node_data(out_id).get_y() + force_vector_components[1] * damping
            )  # calculate the new y coordinate
            new_z = (
                drone_graph.get_node_data(out_id).get_z() + force_vector_components[2] * damping
            )  # calculate the new z coordinate

            drone_graph.get_node_data(out_id).set_x(max(0, min(self.x_size, new_x)))
            drone_graph.get_node_data(out_id).set_y(max(0, min(self.y_size, new_y)))
            if self.z_size:
                drone_graph.get_node_data(out_id).set_z(max(0, min(self.z_size, new_z)))
            damping += 0.5 if damping < 10 else 5
            update_edge_function(out_id)           

    def __str__(self) -> str:
        return f"""
            Field with dimensions: [{self.x_size}, {self.y_size}, {self.z_size}]
            Drones: {str.join(chr(10), [str(d) for d in self.drones])}
        """
