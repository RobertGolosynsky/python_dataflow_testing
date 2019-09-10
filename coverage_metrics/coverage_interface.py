import abc


class Coverage(abc.ABC):

    def total_items_of(self, module_path, of_type=None):
        raise NotImplementedError("Implement this")

    def covered_items_of(self, module_path, of_type=None, selected_node_ids=None) -> dict:
        raise NotImplementedError("Implement this")
