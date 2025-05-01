import rustworkx as rx


class DroneGraph(rx.PyGraph):
    """DroneGraph is a wrapper around rustworkx.PyGraph to provide additional functionality
    and to make it easier to work with drone data. It is used to represent a graph of drones
    and their connections, allowing for operations like adding nodes, edges, and calculating
    distances between them.
    """    
    def __str__(self) -> str:
        """Returns a string representation of the graph, including node data and edges.

        Returns:
            str: A formatted string representing the graph, including node data and edges.
        """        
        ret_str = ""
        neighbor_dict: dict[list[int], list[tuple[int, int, int]]]
        for src_node in self.node_indices():
            ret_str += f"{self.get_node_data(src_node).pretty_print()}\tEdges:\n"
            neighbor_dict = self.adj(src_node)
            for k, v in neighbor_dict.items():
                if k == src_node:
                    continue
                ret_str += f"\t\t{self.get_node_data(k).pretty_print()} distance: {v}\n"
            ret_str += "\n"
        return ret_str
