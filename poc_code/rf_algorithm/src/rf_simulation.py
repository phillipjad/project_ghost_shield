#!/usr/bin/env python

import argparse
import multiprocessing as mp
import signal
import time
from queue import Queue
from threading import Thread
from time import sleep

from constants.messaging_constants import MSG_STR_E, MSG_STR_INT_MAP
from constants.path_constants import SYSTEM_CONFIG_PATH
from controller import start_controller_thread
from drone import start_drone_process
from field import Field
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


def sig_handler(sig: any, frame: any) -> None:
    for p in PROCESS_LIST:
        if p.is_alive():
            p.terminate()
    for p in PROCESS_LIST:
        p.join()
    exit(0)


def register_controller() -> bool:
    signal.signal(signal.SIGINT, signal.SIG_IGN)
    signal.signal(signal.SIGTERM, signal.SIG_IGN)
    try:
        current_location_xyz: list[float, float, float] = get_location() if False else (5, 5, 5)
        ctllr_thread = Thread(
            target=start_controller_thread,
            args=[
                CONTROLLER_CONFIG["id"],
                CONTROLLER_SEND_QUEUE,
                CONTROLLER_RECV_QUEUE,
                *current_location_xyz,
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
        Thread(target=check_drones_registered, args=[return_list], daemon=True).start()
        sleep(0.1)
    num_drones_registered = return_list[0] if return_list else 0
    print(f"Number of drones registered: {num_drones_registered}")
    return num_drones_registered


def populate_graph() -> None:
    global SYS_GRAPH
    try:
        SYS_GRAPH.add_nodes_from()
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


# TODO - Add logic for controller (location, multicast, etc.)


def main(release: bool) -> None:
    global SYS_GRAPH

    signal.signal(signal.SIGINT, signal.SIG_IGN)
    signal.signal(signal.SIGTERM, signal.SIG_IGN)

    try:
        for i in range(len(DRONES_CONFIG)):
            drone_process = (
                mp.Process(target=start_drone_process, args=[f"DRN{i}", 0, 0, 0])
                if not release
                else mp.Process(target=start_drone_process, args=[f"DRN{i}", 0, 0, 0])
            )
            PROCESS_LIST.append(drone_process)
            drone_process.start()

        signal.signal(signal.SIGINT, sig_handler)
        signal.signal(signal.SIGTERM, sig_handler)

        if not register_controller():
            raise RuntimeError("Failed to register controller")
        if not register_drones():
            raise RuntimeError("Failed to register drones")
        if not populate_graph():
            raise RuntimeError("Failed to populate graph")

        drone_field = Field(10, 10, 10, DRONE_LIST)
        drone_field.randomly_place_drones()  # Randomly place drones in field
        update_graph_edges()

        while not drone_field.drones_are_equidistant(SYS_GRAPH, CONTROLLER.get_location()):
            drone_field.space_drones(SYS_GRAPH, update_egress_edges)
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
