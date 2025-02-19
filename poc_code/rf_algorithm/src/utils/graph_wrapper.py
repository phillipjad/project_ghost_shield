import rustworkx as rx

class DroneGraph(rx.PyGraph):
    def __str__(self) -> str:
        ret_str = ""
        neighbor_dict: dict[list[int], list[tuple[int, int, int]]]
        for src_node in self.node_indices():
            ret_str += f'{self.get_node_data(src_node).pretty_print()}\tEdges:\n'
            neighbor_dict = self.adj(src_node)
            for k, v in neighbor_dict.items():
                if k == src_node:
                    continue
                ret_str += f'\t\t{self.get_node_data(k).pretty_print()} distance: {v}\n'
            ret_str += '\n'
        return ret_str
