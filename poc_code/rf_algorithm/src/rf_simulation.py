#!/usr/bin/env python

import argparse
import math
import multiprocessing as mp
import random
import signal
import time
from multiprocessing import Queue
from threading import Thread
from time import sleep
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

get_location: callable = None
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
        drone["id"]: Drone(drone["id"], *get_drone_location(drone["id"],
                           drone["ip"], drone["port"]), drone["ip"], drone["port"], False)
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


def drones_are_equidistant(controller_location: Vector) -> bool:
    global SYS_GRAPH

    distances: list[Distance] = []
    for i in SYS_GRAPH.edges():
        i = cast(Distance, i)
        distance = i.distance_between_vectors_using_abs(controller_location)
        distances.append(distance)

    return distances.count(distances[0]) == len(distances)


def apply_rf_algorithm(field_vector: Vector, idx_to_guidrone: dict[int, object]) -> None:
    global SYS_GRAPH

    x_size, y_size, z_size = field_vector.get_internals_as_tuple()
    max_repulsion_strength = 50.0  # maximum rep
    min_repulsion_strength = 1  # minimum repulsion strength
    repulsion_strength = max_repulsion_strength
    damping = 0.15  # how much of the force to apply
    min_distance = 0.1  # minimum distance between drones
    last_move_map: dict[int, tuple[float, float, float]] = {}
    finished_ids: set[int] = set()
    iterations: int = 0

    for out_id in SYS_GRAPH.node_indices():
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

            curr_force_vector = distance_vector.calculate_force(
                min_distance, repulsion_strength)
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
        new_z = (
            SYS_GRAPH.get_node_data(out_id).get_z() +
            force_vector_components[2] * damping
        )  # calculate the new z coordinate
        print(
            f'Moving drone {out_id} to ({max(0, min(new_x, x_size))}, {max(0, min(new_y, y_size))}, {max(0, min(new_z, z_size))})')
        if (out_id not in last_move_map) or (
            last_move_map[out_id] != (max(0, min(new_x, x_size)), max(
                0, min(new_y, y_size)), max(0, min(new_z, z_size)))
        ):
            if move_drone(SYS_GRAPH.get_node_data(out_id), out_id, max(0, min(new_x, x_size)), max(0, min(new_y, y_size)), max(0, min(new_z, z_size))):
                if out_id in idx_to_guidrone:
                    gui_drone = idx_to_guidrone[out_id]
                    gui_drone.move_to((new_x, new_y, new_z))

                repulsion_strength = repulsion_strength if iterations <= 30 else max(
                    min_repulsion_strength, repulsion_strength * math.exp(-0.001 * iterations))
                damping = max(0.5, 2.0 * math.exp(-0.02 * iterations))
                last_move_map[out_id] = (max(0, min(new_x, x_size)), max(
                    0, min(new_y, y_size)), max(0, min(new_z, z_size)))
        else:
            finished_ids.add(out_id)
        iterations += 1
        print(last_move_map)
        print(finished_ids)


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
        jamming_response = CONTROLLER_RECV_QUEUE.get(block=False)
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
    if jamming_status:
        print(f"Jamming status: {jamming_status}")


def main(release: bool, positions_queue, drones_queue) -> None:
    global SYS_GRAPH
    if release:
        controller_vector = Vector(
            *wifi_locator.get_xyz_from_ip()
        )
    else:
        controller_vector = Vector(5, 5, 5)
    print(f"Controller location: {controller_vector.get_internals_as_tuple()}")

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

        field_dimensions = Vector(
            FIELD_CONFIG["x"], FIELD_CONFIG["y"], FIELD_CONFIG["z"]
        )

        if not register_controller(controller_vector):
            raise RuntimeError("Failed to register controller")
        if not register_drones():
            raise RuntimeError("Failed to register drones")
        if not populate_graph():
            raise RuntimeError("Failed to populate graph")

        # Randomize locations of drones
        for idx, drone in enumerate(SYS_GRAPH.nodes()):
            drone = cast(Drone, drone)
            move_drone(drone, idx, random.random() + controller_vector.x,
                       random.random() + controller_vector.y, random.random() + controller_vector.z)
            positions_queue.put(
                (idx, drone.get_x(), drone.get_y(), drone.get_z()))

        gui_drones = drones_queue.get()

        idx_to_guidrone = {idx: gui_drones[idx]
                           for idx in range(len(gui_drones))}

        while not drones_are_equidistant(controller_vector):
            apply_rf_algorithm(field_dimensions, idx_to_guidrone)
            print("STILL NOT EQUIDISTANT")
            # print(SYS_GRAPH)

        # Drones are equidistant, so now we can enable jamming
        print("EQUIDISTANT!")
        enable_jamming(10.0)

        check_drones_are_jamming()

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
        args=[drones_queue, positions_queue],
        daemon=True
    )
    gui_process.start()

    # Give the GUI time to initialize
    sleep(1)

    try:
        # Run the RF algorithm in the main process
        main(release, positions_queue, drones_queue)
    except Exception as e:
        print(f"Error in main RF thread: {e}")
    finally:
        # Clean up the GUI process when done
        if gui_process.is_alive():
            gui_process.terminate()
            gui_process.join()
