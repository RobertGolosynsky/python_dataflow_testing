import operator
from collections import defaultdict
from abc import ABC, abstractmethod
import networkx as nx

from ctrl_flow import instructions_key, instruction_key, scope_key
from util import pairwise


def instructions_for_node(g, node):
	return g.nodes[node][instructions_key] if instructions_key in g.nodes[node] else []

def has_def(g, node):
    if instruction_key in g.nodes[node]:
        instr = g.nodes[node][instruction_key]

        if instr.opname == "STORE_FAST" or instr.opname == "STORE_ATTR":
            return True
    return False


def has_use(g, node):
    if instruction_key in g.nodes[node]:
        instr = g.nodes[node][instruction_key]

        if instr.opname == "LOAD_FAST" or instr.opname == "LOAD_ATTR":
            return True
    return False


def resolve_target(g, node):
    pred = next(g.predecessors(node))
    pred_instr = g.nodes[pred][instruction_key]

    if pred_instr.opname == "LOAD_FAST":
        return pred_instr.argval
    elif pred_instr.opname == "LOAD_ATTR":
        t = resolve_target(g, pred) + "." + pred_instr.argval
        return t
    else:
        return None


def get_def(g, node):
    if instruction_key in g.nodes[node]:
        instr = g.nodes[node][instruction_key]
        if instr.opname == "STORE_FAST":
            return instr.argval
        if instr.opname == "STORE_ATTR":
            target = resolve_target(g, node)
            if target:
                return target + "." + instr.argval


def get_use(g, node):
    if instruction_key in g.nodes[node]:
        instr = g.nodes[node][instruction_key]
        if instr.opname == "LOAD_FAST":
            return instr.argval
        if instr.opname == "LOAD_ATTR":
            target = resolve_target(g, node)
            if target:
                return target + "." + instr.argval


class Variable:
    def __init__(self, line, file, var, id_=None, scope=None):
        self.line = str(line)
        self.raw_var = var
        self.file = file
        self.id_ = id_
        self.scope = scope
        self.full_var = self.raw_var
        if self.id_ is not None:
            self.full_var = self.full_var.replace("self", str(self.id_))
        if self.scope is not None and "self" not in self.raw_var:
            self.full_var = str(self.file) + "-->" + self.scope + "-->" + self.full_var

    def __str__(self) -> str:
        return "<Variable> line={}, raw_var={}, full_var={},file={}, id_={}, scope={}" \
            .format(self.line, self.raw_var, self.full_var, self.file, self.id_, self.scope)

    def __repr__(self):
        return self.__str__()

    def __eq__(self, other):
        return self.line == other.line \
               and self.raw_var == other.raw_var\
               and self.file == other.file

    def __hash__(self) -> int:
        return hash(self.line + self.raw_var + str(self.file))


class BaseDefUseTree(ABC):
    @abstractmethod
    def predecessors(self, key) -> []:
        pass

    @abstractmethod
    def successors(self, key) -> []:
        pass

    @abstractmethod
    def get_definitions(self, key) -> [Variable]:
        pass

    @abstractmethod
    def get_uses(self, key) -> [Variable]:
        pass

    @abstractmethod
    def keys(self):
        pass


class TraceEntry:
    def __init__(self, line_key, file, deffs, uses, id_=None, scope=None):
        self.line_key = line_key
        self.file = file
        self.deffs = deffs
        self.uses = uses
        self.id_ = id_
        self.scope = scope

    def get_definitions(self):
        return [Variable(self.line_key, self.file, deff, id_=self.id_, scope=self.scope) for deff in self.deffs]

    def get_uses(self):
        return [Variable(self.line_key, self.file, use, id_=self.id_, scope=self.scope) for use in self.uses]


class Trace(BaseDefUseTree):

    def __init__(self):
        self._trace = []
        pass

    def add_trace(self, line, file, deffs, uses, id_=None, scope=None):
        self._trace.append(TraceEntry(line, file, deffs, uses, id_, scope))

    def get_definitions(self, key) -> [Variable]:
        return self._trace[key].get_definitions()

    def get_uses(self, key) -> [Variable]:
        return self._trace[key].get_uses()

    def predecessors(self, key) -> []:
        return [key - 1] if not key == 0 else []

    def successors(self, key) -> []:
        return [key + 1] if not key == len(self._trace) - 1 else []

    def keys(self) -> set:
        return set(range(len(self._trace)))


class LineTree(BaseDefUseTree):

    def __init__(self, g: nx.MultiDiGraph):
        self.g = g

    def _create_instruction_graph(self, key):
        instructions = instructions_for_node(self.g, key)
            #
            # self.g.nodes[key][instructions_key] \
            # if instructions_key in self.g.nodes[key] else []

        instructions_graph = nx.MultiDiGraph()
        instruction_pairs = pairwise(sorted(instructions,
                                            key=operator.attrgetter("offset")))
        for i1, i2 in instruction_pairs:
            instructions_graph.add_edge(i1.offset, i2.offset)
            instructions_graph.nodes[i1.offset][instruction_key] = i1
            instructions_graph.nodes[i2.offset][instruction_key] = i2
        # print(instructions_graph.nodes(data=True))
        return instructions_graph

    def _get_variables(self, key, extractor):
        instructions_graph = self._create_instruction_graph(key)
        deffs = set()
        for node in instructions_graph.nodes():
            extracted_variable = extractor(instructions_graph, node)
            if extracted_variable:
                deffs.add(extracted_variable)
        variables = []

        for deff in deffs:
            variables.append(Variable(key, "self", deff, None, self.g.nodes[key][scope_key]))
        return variables

    def predecessors(self, key) -> []:
        return self.g.predecessors(key)

    def successors(self, key) -> []:
        return self.g.successors(key)

    def get_definitions(self, key) -> [Variable]:
        return self._get_variables(key, get_def)

    def get_uses(self, key) -> [Variable]:
        return self._get_variables(key, get_use)

    def keys(self):
        return set(self.g.nodes())


def reaching_definitions(tree: BaseDefUseTree):
    reach_out = defaultdict(set)
    working_list = tree.keys()
    while len(working_list) > 0:
        a_node = working_list.pop()
        old_val = reach_out[a_node]
        reach_in = set()
        for a_pred in tree.predecessors(a_node):
            reach_in.update(reach_out[a_pred])

        r_out = set()
        var_definitions = tree.get_definitions(a_node)
        if len(var_definitions) > 0:
            for deff in reach_in:
                for var_definition in var_definitions:
                    if not deff.full_var == var_definition.full_var:
                        r_out.add(deff)

            r_out.update(var_definitions)
        else:
            r_out = reach_in

        reach_out[a_node] = r_out

        if not r_out == old_val:
            working_list.update(tree.successors(a_node))

    return reach_out


def definition_use_pairs(tree: BaseDefUseTree):
    pairs = []
    reaching_deffs = reaching_definitions(tree)
    print(reaching_deffs)
    for key in tree.keys():
        uses = tree.get_uses(key)
        if len(uses) > 0:
            reach_in = reaching_deffs[key]
            for deff in reach_in:
                for use in uses:
                    if use.full_var == deff.full_var:
                        pairs.append((deff, use))
    return pairs
