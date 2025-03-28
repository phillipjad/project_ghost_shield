import argparse
import multiprocessing as mp
from queue import Queue
from threading import Thread
import time

from controller import start_controller_thread
from drone import start_drone_process
from field import Field
from helpers.io_helpers import load_system_config
from helpers.path_constants import SYSTEM_CONFIG_PATH
from utils.distance_obj import Distance
from utils.graph_wrapper import DroneGraph
from utils.read_write_lock import RWLock
from utils.vector import Vector
from constants.messaging_constants import ctrl_send_reg_msg

# CONSTANTS
SYS_GRAPH: DroneGraph = DroneGraph(
    # Edges are bi-directional
    multigraph=False
)

# System Config
(MULTICAST_CONFIG, CONTROLLER_CONFIG, DRONES_CONFIG, SENSORS_CONFIG, SYSTEM_CONFIG) = (
    load_system_config(SYSTEM_CONFIG_PATH)
)

GET_LOCATION: callable = None
NUM_EXPECTED_DRONES = DRONES_CONFIG["num_drones"]
REGISTRATION_TIMEOUT = SYSTEM_CONFIG["timeout"]
CONTROLLER_QUEUE = Queue()

def register_controller() -> None:
    """Will need to expand later
    """
    ctllr_thread = Thread(target=start_controller_thread, args=[CONTROLLER_QUEUE], daemon=True)
    ctllr_thread.start()
    return True


def register_drones() -> None:
    global DRONE_LIST
    # In the future this method will actually work to grab all drones in system
    # Either through config or multicast ping
    CONTROLLER_QUEUE.put(ctrl_send_reg_msg) 

    # Wait for drones to register
    num_drones_registered = CONTROLLER_QUEUE.get(block=True, timeout=SYSTEM_CONFIG["timeout"])
    return num_drones_registered


def populate_graph() -> None:
    global DRONE_LIST, SYS_GRAPH
    SYS_GRAPH.add_nodes_from(DRONE_LIST)
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


def main(debug: bool) -> None:
    global SYS_GRAPH, NUM_EXPECTED_DRONES

    for i in range(NUM_EXPECTED_DRONES):
        mp.Process(target=start_drone_process, args=[i, 0, 0, 0]).start() if debug else mp.Process(target=start_drone_process, args=[i, 0, 0, 0]).start()

    if not register_controller():
        raise RuntimeError("Failed to register controller")
    if not register_drones():
        raise RuntimeError("Failed to register drones")
    populate_graph()

    drone_field = Field(10, 10, 10, DRONE_LIST)
    drone_field.randomly_place_drones()  # Randomly place drones in field
    update_graph_edges()

    while not drone_field.drones_are_equidistant(SYS_GRAPH, CONTROLLER.get_location()):
        drone_field.space_drones(SYS_GRAPH, update_egress_edges)
        print("STILL NOT EQUIDISTANT")
        print(SYS_GRAPH)

    print("EQUIDISTANT!")


if __name__ == "__main__":
    mp.set_start_method('spawn')
    parser = argparse.ArgumentParser(
        prog='Project Ghost Shield - RF Simulation',
        description='***Proof of Concept Simulation for Project Ghost Shield***'
    )
    parser.add_argument('-d', '--debug', action='store_true', help='flag denoting whether to run program in debug mode or in release mode.')
    args = parser.parse_args()
    debug = args.debug
    main(debug)
