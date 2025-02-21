from time import sleep

from drone import Drone
from field import Field
from utils.distance_obj import Distance
from utils.graph_wrapper import DroneGraph
from utils.read_write_lock import RWLock

SYS_GRAPH: DroneGraph = DroneGraph(
    # Edges are bi-directional
    multigraph=False
)
DRONE_LIST: list[Drone] = []
MOVING_DRONES: set[Drone] = set()


def mark_drone_moved(drone: Drone) -> None:
    MOVING_DRONES.add(drone)


def register_drones() -> None:
    global DRONE_LIST
    # In the future this method will actually work to grab all drones in system
    # Either through config or multicast ping
    # LOOP CONTROL FLOW
    # d = grab_drone() / wait_for_ping_respone()
    # DRONE_LIST.append(d)

    # Equidistant list of drones
    # DRONE_LIST = [
    #     Drone(0, 3, 3, 3),
    #     Drone(1, 3, -3, -3),
    #     Drone(2, -3, 3, -3),
    #     Drone(3, -3, -3, 3)
    # ]

    DRONE_LIST = [Drone(id, 0, 0, 0) for id in range(4)]


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
            updated_vector = (
                out_d.get_x() - in_d.get_x(),
                out_d.get_y() - in_d.get_y(),
                out_d.get_z() - in_d.get_z(),
            )
            edge_data.update_vector_with_vector(updated_vector, out_d)


def update_graph_edge(node1_id: int, node2_id: int) -> None:
    """Update a single edge's payload based on two provided nodes.
    The first id should be the "dominant" node in the transaction.

    Args:
        node1_id (int): node ID of the first drone.
        node2_id (int): node ID of the second drone.
    """
    global SYS_GRAPH

    drone1 = SYS_GRAPH.get_node_data(node1_id)
    drone2 = SYS_GRAPH.get_node_data(node2_id)
    edge_data: Distance = SYS_GRAPH.get_edge_data(node1_id, node2_id)
    updated_vector = (
        drone1.get_x() - drone2.get_x(),
        drone1.get_y() - drone2.get_y(),
        drone1.get_z() - drone2.get_z(),
    )
    edge_data.update_vector_with_vector(updated_vector, node1_id)


def vector_sum(
    v1: tuple[float, float, float], v2: tuple[float, float, float]
) -> tuple[float, float, float]:
    pass


# TODO - Add logic for controller (location, multicast, etc.)
def main() -> None:
    global DRONE_LIST, SYS_GRAPH
    register_drones()
    populate_graph()

    drone_field = Field(10, 10, None, DRONE_LIST)

    print(drone_field)
    print(SYS_GRAPH)
    drone_field.randomly_place_drones()
    update_graph_edges()
    print(SYS_GRAPH)
    while drone_field.drones_are_equidistant() is not True:
        drone_field.space_drones()
        print("STILL NOT EQUIDISTANT")
        sleep(1)
    else:
        print("EQUIDISTANT!")


if __name__ == "__main__":
    main()
