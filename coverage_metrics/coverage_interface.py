import abc
import itertools

from coverage_metrics.util import percent


class Coverage(abc.ABC):

    def total_items_of(self, module_path, of_type=None):
        raise NotImplementedError("Implement this")

    def covered_items_of(self, module_path, of_type=None, selected_node_ids=None) -> dict:
        raise NotImplementedError("Implement this")

    def coverage_of(self, module_path, of_type=None, selected_node_ids=None) -> int:
        covered_items_per_node_id = self.covered_items_of(
            module_path,
            of_type=of_type,
            selected_node_ids=selected_node_ids
        )
        total_covered_items = set(itertools.chain.from_iterable(covered_items_per_node_id.values()))
        total_possible_items = self.total_items_of(module_path, of_type=of_type)
        return int(percent(total_covered_items, total_possible_items))
