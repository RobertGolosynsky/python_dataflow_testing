import inspect
import operator

from xdis.std import get_instructions, Instruction
from xdis import PYTHON_VERSION, IS_PYPY
from control_flow.bb import basic_blocks
from control_flow.cfg import ControlFlowGraph
from control_flow.graph import BB_JUMP_UNCONDITIONAL, FLAG2NAME, \
    BB_NOFOLLOW, BB_END_FINALLY, BB_FINALLY, BB_STARTS_POP_BLOCK

import networkx as nx
from loguru import logger
from itertools import chain
from collections import namedtuple, defaultdict
from typing import Optional

from graphs.keys import DEFINITION_KEY, USE_KEY, LINE_KEY, INSTRUCTION_KEY, CALLS_KEY, FUNCTION_KEY, REMOVED_KEY, \
    CALL_KEY, RETURN_KEY

FakeBytecodeInstruction = namedtuple("FakeBytecodeInstruction", ["offset", "opname", "argval", "starts_line"])

exit_node_offset = 1


class CFG:

    def __init__(self, g, entry_label, exit_label):
        self.g = g
        self.entry_label = entry_label
        self.exit_label = exit_label

    def extended(self, possible_callees: dict):
        # if not canvas:
        extended = self.copy()
        # else:
        #     canvas.g = nx.compose(canvas.g, self.g)
        # if not included_cfgs:
        included_cfgs = set()  # a set of functions that are already on the canvas
        # if not resolved_call_nodes:
        resolved_call_nodes = set()

        # for every node in parent cfg
        working_list = list(self.g.nodes())

        while working_list:
            node = working_list.pop()
            data = extended.g.nodes[node]
            callee_name = data.get(CALLS_KEY)
            # if there is a call to other method at node
            if callee_name and callee_name.startswith("self."):
                pure_callee_name = callee_name[5:]
                # and we have not yet added that cfg
                if pure_callee_name not in included_cfgs:

                    callee_cfg = possible_callees.get(pure_callee_name)
                    # if there is a cfg for the target function
                    if callee_cfg:
                        # add it so we don't process this function again if it is called elsewhere
                        included_cfgs.add(pure_callee_name)

                        # insert the callee at the caller call site
                        extended.insert_graph_at_node(node, callee_cfg)
                        resolved_call_nodes.add(node)
                        # extend the callee calls
                        working_list.extend(callee_cfg.g.nodes())
                else:
                    # we found a repeating call
                    # this function is already on the canvas graph
                    # just need to hook it up
                    resolved_call_nodes.add(node)
                    # this is only required to figure out the entry and exit labels of the callee
                    callee_cfg = possible_callees.get(pure_callee_name)
                    extended.hook_up_call_site(node, callee_cfg.entry_label, callee_cfg.exit_label)
        g: nx.DiGraph = extended.g
        # g.remove_nodes_from(resolved_call_nodes)
        return extended

    def hook_up_call_site(self, node, sub_graph_entry, sub_graph_exit):

        children = list(self.g.successors(node))

        callee_name = self.g.nodes[sub_graph_entry][FUNCTION_KEY]
        caller_name = self.g.nodes[node][FUNCTION_KEY]

        for edge_to_remove in self.g.out_edges(node, keys=True):
            node_from, node_to, _ = edge_to_remove
            if node_to.startswith(caller_name):
                self.g.edges[edge_to_remove][REMOVED_KEY] = True  # we keep the edge only for display purposes

        # self.g.add_edge(node, sub_graph_entry, label="Call to " + callee_name, color="blue")
        self.g.add_edge(node, sub_graph_entry, **{CALL_KEY: callee_name})

        for child in children:
            if child.startswith(caller_name):
                self.g.add_edge(sub_graph_exit, child, **{RETURN_KEY: caller_name})

    def insert_graph_at_node(self, node, sub_graph):
        # print("graph", self.g.nodes())
        # print("sub_graph", sub_graph.g.nodes())
        self.g = nx.compose(self.g, sub_graph.g)
        # self.g.remove_node(node)
        self.hook_up_call_site(node, sub_graph.entry_label, sub_graph.exit_label)

    def collect_definitions_and_uses(self, filter_self=True):
        definitions = defaultdict(list)
        uses = defaultdict(list)
        for node, node_attrs in self.g.nodes(data=True):
            use = node_attrs.get(USE_KEY, None)
            definition = node_attrs.get(DEFINITION_KEY, None)
            line = node_attrs.get(LINE_KEY, -1)
            if line > -1:
                if definition:
                    definitions[line].append(definition)
                if use:
                    uses[line].append(use)
        return definitions, uses

    def expose_call_sites(self, calls):
        call_dict = defaultdict(list)
        for line, idx, fname in calls:
            call_dict[line].append((idx, fname))

        # sort calls for line by call number (larger first)
        for line_num in call_dict:
            call_dict[line_num] = list(sorted(call_dict[line_num], key=operator.itemgetter(0)))

        for node, data in self.g.nodes(data=True):
            line = data.get(LINE_KEY)
            if line:
                inst = data.get(INSTRUCTION_KEY)
                if inst:
                    opname = inst.opname
                    if opname.startswith("CALL_"):
                        calls_on_line = call_dict.get(line)
                        if calls_on_line:
                            if len(calls_on_line) == 1:
                                _, fname = calls_on_line.pop()
                                data[CALLS_KEY] = fname
                            else:
                                _, fname = calls_on_line.pop()
                                data[CALLS_KEY] = fname

    def copy(self):
        return CFG(self.g.copy(), self.entry_label, self.exit_label)


def try_create_cfg(func, definition_line=None, args=None) -> Optional[CFG]:
    try:
        bb_mgr = basic_blocks(PYTHON_VERSION, IS_PYPY, func)
        cfg = ControlFlowGraph(bb_mgr)

    except Exception:
        logger.exception("Error during CFG creation")
        return None

    byte_blocks_graph = cfg.graph
    g = nx.MultiDiGraph()

    instructions = list(_get_instructions(func, definition_line))

    fake_instructions = _try_fake_instructions_function_arguments(func, definition_line=definition_line, args=args)
    if fake_instructions is None:
        return None
    instructions.extend(fake_instructions)

    offset_to_instruction = {}

    for i in instructions:
        offset_to_instruction[i.offset] = i
        if isinstance(i, Instruction):
            i.argval = 0

    offset_to_line = {}

    for i in instructions:
        offset = i.offset
        instr = i
        while not instr.starts_line:
            offset -= 2
            instr = offset_to_instruction[offset]
        offset_to_line[i.offset] = instr.starts_line

    for instr in instructions:
        attrs = {
            LINE_KEY: offset_to_line[instr.offset],
            INSTRUCTION_KEY: instr
        }
        g.add_node(instr.offset, **attrs)

    for node in byte_blocks_graph.nodes:
        start = node.bb.index[0]
        end = node.bb.index[1]

        source = start
        for offset in range(start + 2, end + 2, 2):
            for ins in instructions:
                if ins.offset == offset:
                    g.add_edge(source, offset)
                    source = offset
    for edge in byte_blocks_graph.edges:
        remove = False
        if edge.kind == 'fallthrough' \
                and \
                BB_JUMP_UNCONDITIONAL in edge.source.flags:
            remove = True
        #
        # if edge.kind == 'fallthrough' \
        #         and \
        #         BB_NOFOLLOW in edge.dest.flags:
        #     remove = True
        if edge.kind == 'no fallthrough':
            remove = True
        # if edge.kind == 'fallthrough':
        #     remove = True
        # if BB_FINALLY in edge.source.flags and BB_END_FINALLY in edge.dest.flags:
        #     remove = True
        # if edge.kind == "forward" and BB_STARTS_POP_BLOCK in edge.dest.flags:
        #     remove = True

        if edge.kind == "exception" and BB_END_FINALLY in edge.dest.flags:
            remove = True
        if edge.kind == "forward" and BB_END_FINALLY in edge.dest.flags:
            remove = True

        if remove:
            continue

        def fl2name(fls):
            return ", ".join([FLAG2NAME[f] for f in fls])

        source = edge.source
        dest = edge.dest
        source_offset = source.bb.index[1]
        dest_offset = dest.bb.index[0]
        # print("%i -> %i" % (source_offset, dest_offset),
        #       "| kind: " + edge.kind +
        #       " | source flags: " +
        #       str(fl2name(edge.source.flags)) +
        #       " | dest flags: " +
        #       str(fl2name(edge.dest.flags))
        #       )
        if not dest_offset % 2 == 0:  # maybe don't add an extra node for exit?
            g.add_edge(source_offset, exit_node_offset,
                       label=edge.kind + " / " + str(fl2name(edge.source.flags)) + " / " + str(
                           fl2name(edge.dest.flags)),
                       source_flags=fl2name(edge.source.flags),
                       dest_flags=fl2name(edge.dest.flags),
                       color="red" if remove else "black"
                       )
        else:
            # colors = ['#35332C', '#E1DAC2', '#D1B04B', '#3C2E00', '#C19200', '#242C24', '#A1B99F', '#48AB3D', '#053200',
            #           '#0F9E00', '#352D2C', '#E1C6C2', '#D15A4B', '#3C0700', '#C11600', '#201F25', #'#8B8B9D', '#454292',
            #           '#02002A', '#0C0787']
            colors = ["red", "yellow", "blue", "orange", "purple", "brown"]
            g.add_edge(source_offset, dest_offset,
                       label=edge.kind + " / " + str(fl2name(edge.source.flags)) + " / " + str(
                           fl2name(edge.dest.flags)),
                       source_flags=fl2name(edge.source.flags),
                       dest_flags=fl2name(edge.dest.flags),
                       # color="red" if remove else "black"
                       color=colors[hash(edge.kind) % len(colors)],
                       weight=10000
                       )
    entry_node_label = 0
    if len(fake_instructions) > 0:
        fake_instructions = list(sorted(fake_instructions, key=lambda i: i.offset))
        entry_node_label = fake_instructions[0].offset
        for i1, i2 in zip(fake_instructions, fake_instructions[1:]):
            g.add_edge(i1.offset, i2.offset)

        last_fake_instruction_offset = fake_instructions[-1].offset
        first_real_instruction_offset = 0

        g.add_edge(last_fake_instruction_offset, first_real_instruction_offset)

    exit_node_label = 1
    function_name = func.__name__

    def rename_node(node):
        return function_name + "@" + str(node)

    mapping = {node: rename_node(node) for node in g.nodes()}
    nx.relabel_nodes(g, mapping=mapping, copy=False)
    nx.set_node_attributes(g, function_name, FUNCTION_KEY)

    return CFG(g, rename_node(entry_node_label), rename_node(exit_node_label))


def _try_fake_instructions_function_arguments(func, definition_line=None, args=None):
    # print(func, definition_line, args)
    if not definition_line:
        try:
            _, definition_line = inspect.getsourcelines(func)
        except:
            return None

    if args is None:
        arg_spec = inspect.getfullargspec(func)

        args = arg_spec.args

        if arg_spec.varargs:
            args.append(arg_spec.varargs)
        if arg_spec.varkw:
            args.append(arg_spec.varkw)

    instructions = []
    max_offset = 0
    for i, arg in enumerate(args[1:]):
        if not arg == "self":
            fake_offset = -2 - i * 2
            fake_instruction = FakeBytecodeInstruction(fake_offset, "STORE_FAST", arg, False)
            instructions.append(fake_instruction)
            max_offset = fake_offset
    if len(args) > 0:
        instruction_with_line = FakeBytecodeInstruction(
            max_offset - 2,
            "STORE_FAST",
            args[0],
            definition_line
        )
        instructions.append(instruction_with_line)

    return instructions


def _get_instructions(func, definition_line=None):
    instrs = []
    for ins in get_instructions(func, first_line=None):
        argval = None
        if isinstance(ins.argval, str) or isinstance(ins.argval, int):
            argval = ins.argval
        fake = FakeBytecodeInstruction(ins.offset, ins.opname, argval, ins.starts_line)
        instrs.append(fake)
    return instrs
