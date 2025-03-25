from controller import Controller
from drone import Drone
from field import Field
from utils.distance_obj import Distance
from utils.graph_wrapper import DroneGraph
from utils.read_write_lock import RWLock
from utils.vector import Vector

SYS_GRAPH: DroneGraph = DroneGraph(
    # Edges are bi-directional
    multigraph=False
)
DRONE_LIST: list[Drone] = []
MOVING_DRONES: set[Drone] = set()
CONTROLLER: Controller = None
# TODO
GET_LOCATION: callable = None


def mark_drone_moved(drone: Drone) -> None:
    MOVING_DRONES.add(drone)


def register_controller() -> None:
    global CONTROLLER
    """Will need to expand later
    """
    curr_location = GET_LOCATION if False else (5, 5, 5)
    if CONTROLLER is None:
        CONTROLLER = Controller(*curr_location)


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
            # skips reverse edges that are already in the graph, added for effciency
            if out_d.equals(in_d):
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


# only updates edges between moving drones, added for effciency
def update_moving_drones_edges() -> None:
    global SYS_GRAPH, MOVING_DRONES

    for drone in MOVING_DRONES:
        if drone not in SYS_GRAPH.nodes():
            raise ValueError(f"Drone {drone.get_id()} not found in graph")
        for in_idx, in_d in SYS_GRAPH.nodes():
            if drone.equals(in_d):
                continue
            edge_data = SYS_GRAPH.get_edge_data(drone.get_id, in_idx)
            updated_vector: Vector = Vector(
                drone.get_x() - in_d.get_x(),
                drone.get_y() - in_d.get_y(),
                drone.get_z() - in_d.get_z(),
            )
            edge_data.update_vector_with_vector(updated_vector, drone)


def update_graph_edges() -> None:
    """
    Updates the edges of the graph with the current distance between every Drone.
    """
    global SYS_GRAPH

    for out_idx, out_d in enumerate(SYS_GRAPH.nodes()):
        for in_idx, in_d in enumerate(SYS_GRAPH.nodes()):
            if out_d.equals(in_d):
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


def main() -> None:
    global DRONE_LIST, SYS_GRAPH
    register_controller()
    register_drones()  # ex: [Drone(0, 3, 3, 3), Drone(1, 3, -3, -3), Drone(2, -3, 3, -3), Drone(3, -3, -3, 3)]
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
    main()
