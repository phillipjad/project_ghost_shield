#!/usr/bin/env python

import argparse
import math
import multiprocessing as mp
import random
import signal
import time
from multiprocessing import Queue
from threading import Thread
from typing import cast
import simulation

from constants.messaging_constants import MSG_STR_E, MSG_STR_INT_MAP
from constants.path_constants import SYSTEM_CONFIG_PATH
from controller import start_controller_thread
from drone import Drone, start_drone_process
from helpers.io_helpers import load_system_config
from utils.distance_obj import Distance
from utils.graph_wrapper import DroneGraph
from utils.read_write_lock import RWLock
from utils.vector import Vector
from wifi_lib import wifi_locator

positions_queue: Queue = Queue()  # RF -> GUI
drones_queue: Queue = Queue()     # GUI -> RF
movement_queue = mp.Queue()       # For sending movement commands to GUI

# CONSTANTS
SYS_GRAPH: DroneGraph = DroneGraph(
    # Edges are bi-directional
    multigraph=False
)

# System Config
(
    MULTICAST_CONFIG,
    CONTROLLER_CONFIG,
    DRONES_CONFIG,
    SENSORS_CONFIG,
    SYSTEM_CONFIG,
    FIELD_CONFIG,
) = load_system_config(SYSTEM_CONFIG_PATH)

REGISTRATION_TIMEOUT = SYSTEM_CONFIG["timeout_s"]
CONTROLLER_SEND_QUEUE = Queue()
CONTROLLER_RECV_QUEUE = Queue()
PROCESS_LIST: list[mp.Process] = []
DRONE_MAP: dict[str, Drone] = {}


def sig_handler(sig: any, frame: any) -> None:
    for p in PROCESS_LIST:
        if p.is_alive():
            p.terminate()
    for p in PROCESS_LIST:
        p.join()
    exit(0)


def register_controller(controller_vector: Vector) -> bool:
    signal.signal(signal.SIGINT, signal.SIG_IGN)
    signal.signal(signal.SIGTERM, signal.SIG_IGN)
    try:
        ctllr_thread = Thread(
            target=start_controller_thread,
            args=[
                CONTROLLER_CONFIG["id"],
                CONTROLLER_SEND_QUEUE,
                CONTROLLER_RECV_QUEUE,
                *controller_vector.get_internals_as_tuple(),
                CONTROLLER_CONFIG["ip"],
                CONTROLLER_CONFIG["port"],
            ],
            daemon=True,
        )
        ctllr_thread.start()
        return True
    except Exception:
        return False
    finally:
        signal.signal(signal.SIGINT, sig_handler)
        signal.signal(signal.SIGTERM, sig_handler)


def check_drones_registered(return_list: list[int]) -> None:
    try:
        num_drones_registered = CONTROLLER_RECV_QUEUE.get()
        return_list.append(num_drones_registered)
        return
    except Exception:
        return


def register_drones() -> int:
    global CONTROLLER_SEND_QUEUE, CONTROLLER_RECV_QUEUE

    CONTROLLER_SEND_QUEUE.put(
        (
            MSG_STR_INT_MAP.get(MSG_STR_E.ENABLE_REGISTRATION),
            [CONTROLLER_CONFIG["id"]],
            REGISTRATION_TIMEOUT,
        )
    )

    return_list: list[int] = []
    # Wait for drones to register
    check_drones_registered_thread = Thread(
        target=check_drones_registered, args=[return_list], daemon=True)
    check_drones_registered_thread.start()
    check_drones_registered_thread.join(REGISTRATION_TIMEOUT)
    num_drones_registered = return_list[0] if return_list else 0
    print(f"Number of drones registered: {num_drones_registered}")
    return num_drones_registered == len(DRONES_CONFIG)


def check_location_response(return_list: list[tuple[float, float, float]]) -> None:
    try:
        location_response = CONTROLLER_RECV_QUEUE.get()
        return_list.append(location_response)
        return
    except Exception:
        return


def get_drone_location(drone_id: str, drone_ip: str, drone_port: int) -> tuple[float, float, float] | None:
    """Get the location of a drone by its address.

    Args:
        drone_id (str): The ID of the drone.

    Returns:
        tuple[float, float, float]: The x, y, z coordinates of the drone.
    """
    global CONTROLLER_SEND_QUEUE, CONTROLLER_RECV_QUEUE

    CONTROLLER_SEND_QUEUE.put(
        (
            MSG_STR_INT_MAP.get(MSG_STR_E.GET_LOCATION),
            [CONTROLLER_CONFIG["id"]],
            [drone_ip, drone_port],
        )
    )

    return_list = []
    check_location_thread = Thread(target=check_location_response, args=[
                                   return_list], daemon=True)
    check_location_thread.start()
    check_location_thread.join(10)
    drone_location = return_list[0] if return_list else None
    return drone_location


def get_drones(drones_config: list[dict]) -> dict[str, Drone]:
    """Get the locations of all drones in the system and returns them as non-process Drone objects #TODO - Make separate Drone class.

    Args:
        drones_config (list[dict]): List of drone configurations.

    Returns:
        dict[str, Drone]: Dictionary of drone IDs and their corresponding Drone objects.
    """
    return {
        drone["id"]: Drone(
            drone["id"], *get_drone_location(drone["id"], drone["ip"], drone["port"]), drone["ip"], drone["port"], False
        )
        for drone in drones_config
    }


def move_drone(drone: Drone, node_id: int, x: float, y: float, z: float) -> bool:
    """Move a drone to a new location.

    Args:
        drone (Drone): The drone to move.
        x (float): The new x coordinate.
        y (float): The new y coordinate.
        z (float): The new z coordinate.
    """
    try:
        CONTROLLER_SEND_QUEUE.put(
            (
                MSG_STR_INT_MAP.get(MSG_STR_E.MOVE_LOCATION),
                [CONTROLLER_CONFIG["id"], x, y, z],
                [drone.drone_tcp_ip, drone.drone_tcp_port],
            )
        )
        return_list = []
        check_location_thread = Thread(target=check_location_response, args=[
                                       return_list], daemon=True)
        check_location_thread.start()
        check_location_thread.join(10)
        drone_location = return_list[0] if return_list else None
        if drone_location:
            x, y, z = drone_location
            drone.set_x(x)
            drone.set_y(y)
            drone.set_z(z)
            update_egress_edges(node_id)
            return True
    except Exception as e:
        print(f"Error moving drone {drone.get_id()}: {e}")
        return False


def populate_graph(refresh: bool = False) -> True:
    global SYS_GRAPH, DRONE_MAP

    try:
        # Return a list in tuple[<id, x, y, z>] format
        DRONE_MAP = get_drones(DRONES_CONFIG)
        if refresh:
            SYS_GRAPH.clear()
        SYS_GRAPH.add_nodes_from(list(DRONE_MAP.values()))
        for out_idx, out_d in enumerate(SYS_GRAPH.nodes()):
            for in_idx, in_d in enumerate(SYS_GRAPH.nodes()):
                if out_d == in_d:
                    continue
                edge_data = Distance(
                    out_d.get_x() - in_d.get_x(),
                    out_d.get_y() - in_d.get_y(),
                    out_d.get_z() - in_d.get_z(),
                    RWLock(),
                    out_idx,
                )
                SYS_GRAPH.add_edge(
                    out_idx,
                    in_idx,
                    edge_data,
                )
        return True
    except Exception as e:
        print(f"Error populating graph: {e}")
        return False


def update_graph_edges() -> None:
    """
    Updates the edges of the graph with the current distance between every Drone.
    """
    global SYS_GRAPH

    for out_idx, out_d in enumerate(SYS_GRAPH.nodes()):
        for in_idx, in_d in enumerate(SYS_GRAPH.nodes()):
            if out_d == in_d:
                continue
            edge_data: Distance = SYS_GRAPH.get_edge_data(out_idx, in_idx)
            updated_vector: Vector = Vector(
                out_d.get_x() - in_d.get_x(),
                out_d.get_y() - in_d.get_y(),
                out_d.get_z() - in_d.get_z(),
            )
            edge_data.update_vector_with_vector(updated_vector, out_d)


def update_graph_edge(node1_id: int, node2_id: int, edge_data: Distance) -> None:
    """Update a single edge's payload based on two provided nodes.
    The first id should be the "dominant" node in the transaction.

    Args:
        node1_id (int): node ID of the first drone.
        node2_id (int): node ID of the second drone.
    """
    global SYS_GRAPH

    drone1 = SYS_GRAPH.get_node_data(node1_id)
    drone2 = SYS_GRAPH.get_node_data(node2_id)
    updated_vector = Vector(
        drone1.get_x() - drone2.get_x(),
        drone1.get_y() - drone2.get_y(),
        drone1.get_z() - drone2.get_z(),
    )
    edge_data.update_vector_with_vector(updated_vector, node1_id)


def update_egress_edges(node_id: int) -> None:
    global SYS_GRAPH
    edges: list[tuple[int, int, Distance]] = SYS_GRAPH.out_edges(node_id)
    for edge in edges:
        update_graph_edge(edge[0], edge[1], edge[2])


def drones_are_spaced_properly(controller_location: Vector, two_recent_distance_magnitudes: list[float, float], tolerance: float) -> bool:
    global SYS_GRAPH

    magnitude_sum: float = 0.0
    distances: list[Distance] = []
    for i in SYS_GRAPH.nodes():
        drone_location: Vector = Vector(i.get_x(), i.get_y(), i.get_z())
        distance = drone_location.as_abs().distance_between_vector(controller_location)
        magnitude_sum += drone_location.as_abs().get_magnitude()
        distances.append(distance)

    two_recent_distance_magnitudes[0] = two_recent_distance_magnitudes[1]
    two_recent_distance_magnitudes[1] = magnitude_sum
    mean_distance: float = sum(distances) / len(distances)
    return all(abs(d - mean_distance) < tolerance for d in distances)


def all_drones_stable(last_move_map: dict[str, tuple[float, float, float]], threshold: float = 0.01) -> bool:
    return all(
        (x**2 + y**2 + z**2)**0.5 < threshold
        for x, y, z in last_move_map.values()
    )

def clamp_position_to_radius(vector: Vector, controller_vector: Vector, force_function: callable = lambda ic, f, d: calculate_force_severe_dropoff(ic, f, d), max_radius: float = 30.0) -> Vector:
    to_controller = vector.vector_sum(controller_vector.as_negated())
    if to_controller.get_magnitude() > max_radius:
        # Pull gently toward the controller
        return to_controller.calculate_force(0.01, 1.0, force_function).as_negated()
    return Vector(0.0, 0.0, 0.0)



def calculate_force_severe_dropoff(
    inner_components: tuple[float, float, float], distance: float, force: float
) -> Vector:
    """Calculates a force vector based on the calling Vector's internal state,

    Args:
        inner_components (tuple[float, float, float]): Tuple of the x, y, z components of the vector.
        distance (float): The distance between the two vectors.
        force (float): The force to apply.

    Returns:
        Vector: A vector with the force applied in the direction of the inner components.
    """
    return Vector(
        ((inner_components[0] / distance) * force),
        ((inner_components[1] / distance) * force),
        ((inner_components[2] / distance) * force),
    )


def calculate_force_soft_dropoff(inner_components: tuple[float, float, float], distance: float, force: float) -> Vector:
    """Calculates a force vector based on the calling Vector's internal state,

    Args:
        inner_components (tuple[float, float, float]): Tuple of the x, y, z components of the vector.
        distance (float): The distance between the two vectors.
        force (float): The force to apply.

    Returns:
        Vector: A vector with the force applied in the direction of the inner components.
    """
    return Vector(
        ((inner_components[0] / math.sqrt(distance + 1e-6)) * force),
        ((inner_components[1] / math.sqrt(distance + 1e-6)) * force),
        ((inner_components[2] / math.sqrt(distance + 1e-6)) * force),
    )


def calculate_force_log_dropoff(inner_components: tuple[float, float, float], distance: float, force: float) -> Vector:
    """Calculates a force vector based on the calling Vector's internal state,

    Args:
        inner_components (tuple[float, float, float]): Tuple of the x, y, z components of the vector.
        distance (float): The distance between the two vectors.
        force (float): The force to apply.

    Returns:
        Vector: A vector with the force applied in the direction of the inner components.
    """
    return Vector(
        ((inner_components[0] / math.log1p(distance)) * force),
        ((inner_components[1] / math.log1p(distance)) * force),
        ((inner_components[2] / math.log1p(distance)) * force),
    )


def apply_rf_algorithm(
    operational_ceiling: int,
    field_vector: Vector,
    controller_vector: Vector,
    last_move_map: dict[str, tuple[float, float, float]],
    finished_ids: set[int],
) -> None:
    global SYS_GRAPH

    controller_x, controller_y, controller_z = controller_vector.get_internals_as_tuple()
    field_x, field_y, field_z = field_vector.get_internals_as_tuple()
    min_x_bound = controller_x - field_x / 2
    min_y_bound = controller_y - field_y / 2
    max_x_bound = controller_x + field_x / 2
    max_y_bound = controller_y + field_y / 2
    max_z_bound = controller_z + operational_ceiling
    max_repulsion_strength = 5.0  # maximum rep
    min_repulsion_strength = 1  # minimum repulsion strength
    repulsion_strength = max_repulsion_strength
    damping = 0.5  # how much of the force to apply
    min_distance = 0.1  # minimum distance between drones
    collision_min_distance = ((field_x * field_y * (field_z/2)) / SYS_GRAPH.num_nodes())**(1/3)
    iterations: int = 0

    for out_id in SYS_GRAPH.node_indices():
        force_function: callable
        if (len(finished_ids) < (SYS_GRAPH.num_nodes()/4)):
            force_function = calculate_force_log_dropoff
        elif (len(finished_ids) < (SYS_GRAPH.num_nodes()/2)):
            force_function = calculate_force_soft_dropoff
        else:
            force_function = calculate_force_severe_dropoff
        if out_id in finished_ids:  # skip if already processed
            continue
        force_vector = Vector(0.0, 0.0, 0.0)  # there is no force initially

        for in_id in SYS_GRAPH.node_indices():
            if out_id == in_id:  # skip if it is the same drone
                continue

            edge_data: Distance = SYS_GRAPH.get_edge_data(out_id, in_id)
            distance_vector = edge_data.get_vector()
            if edge_data.get_last_to_write() != out_id:
                distance_vector = distance_vector.as_negated()

            curr_force_vector = distance_vector.calculate_force(collision_min_distance, repulsion_strength, force_function)
            force_vector.mutating_vector_sum(curr_force_vector)
        force_vector_components = force_vector.get_internals_as_tuple()
        new_x = (
            SYS_GRAPH.get_node_data(out_id).get_x() +
            force_vector_components[0] * damping
        )  # calculate the new x coordinate
        new_y = (
            SYS_GRAPH.get_node_data(out_id).get_y() +
            force_vector_components[1] * damping
        )  # calculate the new y coordinate

        new_location = Vector(
            max(min_x_bound, min(new_x, max_x_bound)), max(min_y_bound, min(new_y, max_y_bound)), max_z_bound
        )

        for in_id in SYS_GRAPH.node_indices():
            if out_id == in_id:
                continue
            other_drone = SYS_GRAPH.get_node_data(in_id)
            other_location = Vector(other_drone.get_x(), other_drone.get_y(), other_drone.get_z())
            while new_location.distance_between_vector(other_location) < collision_min_distance:
                num_drones = SYS_GRAPH.num_nodes()
                attempted_x, attempted_y, _ = new_location.get_internals_as_tuple()
                new_location = Vector(
                    max(min_x_bound, min(attempted_x + random.uniform(-(field_x / num_drones), field_x / num_drones), max_x_bound)),
                    max(min_y_bound, min(attempted_y + random.uniform(-(field_y / num_drones), field_y / num_drones), max_y_bound)),
                    max_z_bound,
                )

        print(f"Drone {out_id} moving to {new_location.get_internals_as_tuple()}")
        if (out_id not in last_move_map) or (last_move_map.get(out_id) != new_location.get_internals_as_tuple()):
            if move_drone(SYS_GRAPH.get_node_data(out_id), out_id, *new_location.get_internals_as_tuple()):
                repulsion_strength = max(min_repulsion_strength, repulsion_strength * math.exp(-0.001 * iterations))
                # damping = max(0.5, 2.0 * math.exp(-0.02 * iterations))
                last_move_map[out_id] = new_location.get_internals_as_tuple()
        elif new_location.get_internals_as_tuple() not in last_move_map.values():
            finished_ids.add(out_id)
        iterations += 1


def enable_jamming(duration: float) -> None:
    CONTROLLER_SEND_QUEUE.put(
        (
            MSG_STR_INT_MAP.get(MSG_STR_E.ENABLE_JAMMER),
            [CONTROLLER_CONFIG["id"], duration],
            duration,
        )
    )


def check_jamming_response(return_list: list[bool], num_drones: int) -> None:
    try:
        jamming_response = CONTROLLER_RECV_QUEUE.get()
        return_list.append(jamming_response)
        if (len(return_list) == num_drones) and all(return_list):
            return
    except Exception:
        return


def check_drones_are_jamming() -> None:
    return_list = []
    check_jamming_thread = Thread(target=check_jamming_response, args=[
                                  return_list, len(DRONES_CONFIG)], daemon=True)
    check_jamming_thread.start()
    check_jamming_thread.join(10)
    jamming_status = return_list[0] if return_list else False
    print(f"Jamming status: {jamming_status}")


def main(release: bool, positions_queue, drones_queue) -> None:
    global SYS_GRAPH
    controller_vector: Vector
    if release:
        controller_vector = Vector(*wifi_locator.get_xyz_from_ip())
    else:
        controller_vector = Vector(5, 5, 5)
    print(f"Controller location: {controller_vector.get_internals_as_tuple()}")
    last_move_map: dict[str, tuple[float, float, float]] = {}
    finished_ids: set[int] = set()
    two_recent_distance_magnitudes: list[float, float] = [-1.0, -2.0]
    field_dimensions = Vector(FIELD_CONFIG["x"], FIELD_CONFIG["y"], FIELD_CONFIG["z"])
    operational_ceiling: int = SYSTEM_CONFIG["operational_ceiling"]
    temperature: float = max(field_dimensions.x, field_dimensions.y, operational_ceiling) / 10.0

    signal.signal(signal.SIGINT, signal.SIG_IGN)
    signal.signal(signal.SIGTERM, signal.SIG_IGN)

    try:
        for drone_config in DRONES_CONFIG:
            drone_process = mp.Process(
                target=start_drone_process,
                args=[
                    drone_config["id"],
                    0,
                    0,
                    0,
                    drone_config["ip"],
                    drone_config["port"],
                    CONTROLLER_CONFIG["ip"],
                    CONTROLLER_CONFIG["port"],
                ],
            )
            PROCESS_LIST.append(drone_process)
            drone_process.start()

        signal.signal(signal.SIGINT, sig_handler)
        signal.signal(signal.SIGTERM, sig_handler)


        if not register_controller(controller_vector):
            raise RuntimeError("Failed to register controller")
        if not register_drones():
            raise RuntimeError("Failed to register drones")
        if not populate_graph():
            raise RuntimeError("Failed to populate graph")

        # Randomize locations of drones
        for idx, drone in enumerate(SYS_GRAPH.nodes()):
            drone = cast(Drone, drone)
            move_drone(
                drone,
                idx,
                random.random() + controller_vector.x,
                random.random() + controller_vector.y,
                random.random() + controller_vector.z,
            )

        s = time.perf_counter()
        while True:
            apply_rf_algorithm(operational_ceiling, field_dimensions, controller_vector, last_move_map, finished_ids)
            temperature = max(temperature * 0.9, 0.01)
            if drones_are_spaced_properly(controller_vector, two_recent_distance_magnitudes, 0.5) or (
                (two_recent_distance_magnitudes[0] > 0 and two_recent_distance_magnitudes[1] > 0)
                or all_drones_stable(last_move_map, 0.1)
            ):
                break
        print(f"Time taken to space: {time.perf_counter() - s:.2f} seconds")

        # Drones are equidistant, so now we can enable jamming
        print("Spaced! Begin jamming")
        enable_jamming(10.0)

        check_drones_are_jamming()

        # 🔁 RETURN TO LAUNCH (RTL)
        print("Returning all drones to controller's location...")
        for drone in DRONE_MAP.values():
            CONTROLLER_SEND_QUEUE.put((
                MSG_STR_INT_MAP[MSG_STR_E.RETURN_TO_LAUNCH],
                [drone.get_id(), drone.drone_tcp_ip, drone.drone_tcp_port],
                None
            ))

        # Give drones time to return before shutdown (optional)
        time.sleep(2)

        sig_handler(None, None)
    except KeyboardInterrupt:
        sig_handler(None, None)
    except Exception as e:
        print(f"Unhandled exception: {e}")
        sig_handler(None, None)


if __name__ == "__main__":
    mp.set_start_method("spawn", force=True)
    parser = argparse.ArgumentParser(
        prog="Project Ghost Shield - RF Simulation",
        description="***Proof of Concept Simulation for Project Ghost Shield***",
    )
    parser.add_argument(
        "-r",
        "--release",
        action="store_true",
        help="If flag is set to true, it runs the program in release mode instead of debug.",
    )
    args = parser.parse_args()
    release = args.release

    # Start the GUI in a separate process
    gui_process = mp.Process(
        target=simulation.main,
        args=[drones_queue, positions_queue, movement_queue],
        daemon=True
    )
    gui_process.start()
    PROCESS_LIST.append(gui_process)

    # Give the GUI time to initialize
    sleep(1)

    try:
        # Run the RF algorithm in the main process
        main(release, positions_queue, drones_queue)
    except Exception as e:
        print(f"Error in main RF thread: {e}")
