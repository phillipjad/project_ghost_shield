#!/usr/bin/env python

import argparse
import multiprocessing as mp
import random
import signal
import time
from queue import Queue
from threading import Thread
from time import sleep
from typing import cast

from constants.messaging_constants import MSG_STR_E, MSG_STR_INT_MAP
from constants.path_constants import SYSTEM_CONFIG_PATH
from controller import start_controller_thread
from drone import Drone, start_drone_process
from helpers.io_helpers import load_system_config
from utils.distance_obj import Distance
from utils.graph_wrapper import DroneGraph
from utils.read_write_lock import RWLock
from utils.vector import Vector

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
        num_drones_registered = CONTROLLER_RECV_QUEUE.get(block=False)
        return_list.append(num_drones_registered)
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
    timeout = time.time() + REGISTRATION_TIMEOUT
    while time.time() <= timeout:
        if return_list:
            break
        Thread(target=check_drones_registered, args=[return_list], daemon=True).start()
        sleep(0.1)
    num_drones_registered = return_list[0] if return_list else 0
    print(f"Number of drones registered: {num_drones_registered}")
    return num_drones_registered


def check_location_response(return_list: list[tuple[float, float, float]]) -> None:
    try:
        location_response = CONTROLLER_RECV_QUEUE.get(block=False)
        return_list.append(location_response)
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
    timeout = time.time() + 10
    while time.time() <= timeout:
        if return_list:
            break
        Thread(target=check_location_response, args=[return_list], daemon=True).start()
        sleep(0.1)
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
        drone["id"]: Drone(drone["id"], *get_drone_location(drone["id"], drone["ip"], drone["port"]), drone["ip"], drone["port"], False)
        for drone in drones_config
    }

def move_drone(drone_id: str, x: float, y: float, z: float) -> None:
    """Move a drone to a new location.

    Args:
        drone (Drone): The drone to move.
        x (float): The new x coordinate.
        y (float): The new y coordinate.
        z (float): The new z coordinate.
    """
    try:
        drone = DRONE_MAP[drone_id]
        d_index: int = [index for index, d in enumerate(DRONES_CONFIG) if d["id"] == drone.get_id()][0]
        ip: str = DRONES_CONFIG[d_index]["ip"]
        port: str = DRONES_CONFIG[d_index]["port"]
        CONTROLLER_SEND_QUEUE.put(
            (
                MSG_STR_INT_MAP.get(MSG_STR_E.MOVE_LOCATION),
                [CONTROLLER_CONFIG["id"], x, y, z],
                [ip, port],
            )
        )
        return_list = []
        timeout = time.time() + 10
        while time.time() <= timeout:
            if return_list:
                break
            Thread(target=check_location_response, args=[return_list], daemon=True).start()
            sleep(0.1)
        drone_location = return_list[0] if return_list else None
        if drone_location:
            x, y, z = drone_location
            drone.set_x(x)
            drone.set_y(y)
            drone.set_z(z)
    except Exception as e:
        print(f"Error moving drone {drone.get_id()}: {e}")
        return


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


# TODO - Add function to only update edges between two specfic nodes
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

def space_drones(field_vector: Vector, drone_graph: DroneGraph) -> None:
    x_size, y_size, z_size = field_vector.get_internals_as_tuple()
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

        drone_graph.get_node_data(out_id).set_x(max(0, min(x_size, new_x)))
        drone_graph.get_node_data(out_id).set_y(max(0, min(y_size, new_y)))
        if z_size:
            drone_graph.get_node_data(out_id).set_z(max(0, min(z_size, new_z)))
        damping += 0.5 if damping < 10 else 5
        update_egress_edges(out_id)

def main(release: bool) -> None:
    global SYS_GRAPH

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

        controller_vector = Vector(
            CONTROLLER_CONFIG["x"], CONTROLLER_CONFIG["y"], CONTROLLER_CONFIG["z"]
        )
        field_dimensions = Vector(
            FIELD_CONFIG["x"], FIELD_CONFIG["y"], FIELD_CONFIG["z"]
        )

        if not register_controller(controller_vector):
            raise RuntimeError("Failed to register controller")
        if not register_drones():
            raise RuntimeError("Failed to register drones")
        if not populate_graph():
            raise RuntimeError("Failed to populate graph")

        print(SYS_GRAPH)

        # Randomize locations of drones
        for idx, drone in enumerate(SYS_GRAPH.nodes()):
            drone = cast(Drone, drone)
            move_drone(drone.get_id(), random.random(), random.random(), random.random())
            update_egress_edges(idx)


        print(SYS_GRAPH)

        # drone_field = Field(FIELD_CONFIG["x"], FIELD_CONFIG["y"], FIELD_CONFIG["z"], DRONE_LIST)
        # drone_field.randomly_place_drones()  # Randomly place drones in field

        while not drones_are_equidistant(SYS_GRAPH, controller_vector):
            space_drones(field_dimensions, update_egress_edges)
            print("STILL NOT EQUIDISTANT")
            print(SYS_GRAPH)

        print("EQUIDISTANT!")
    except KeyboardInterrupt:
        sig_handler(None, None)
    except Exception as e:
        print(f"Unhandled exception: {e}")
        sig_handler(None, None)


if __name__ == "__main__":
    mp.set_start_method("spawn")
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
    main(release)
