import inspect

from xdis.std import get_instructions, Instruction
from xdis import PYTHON_VERSION, IS_PYPY
from control_flow.bb import basic_blocks
from control_flow.cfg import ControlFlowGraph
from control_flow.graph import BB_JUMP_UNCONDITIONAL, FLAG2NAME, \
    BB_NOFOLLOW, BB_END_FINALLY, BB_FINALLY, BB_STARTS_POP_BLOCK

import networkx as nx
from loguru import logger

from collections import namedtuple, defaultdict
from typing import Optional

from graphs.keys import DEFINITION_KEY, USE_KEY, LINE_KEY, INSTRUCTION_KEY, CALLS_KEY

FakeBytecodeInstruction = namedtuple("FakeBytecodeInstruction", ["offset", "opname", "argval", "starts_line"])

exit_node_offset = 1


class CFG:

    def __init__(self, g, entry_label, exit_label):
        self.g = g
        self.entry_label = entry_label
        self.exit_label = exit_label

    def extended(self, possible_callees: dict, canvas=None, included_cfgs=None):
        if not canvas:
            canvas = self.copy()
        if not included_cfgs:
            included_cfgs = set()  # a set of functions that are already on the canvas

        # for every node in parent cfg
        for node, data in self.g.nodes(data=True):

            callee_name = data.get(CALLS_KEY)
            # if there is a call to other function at node
            if callee_name:

                # and we have not yet added that cfg
                if callee_name not in included_cfgs:
                    callee_cfg = possible_callees.get(callee_name)
                    # if there is a cfg for the target function
                    if callee_cfg:
                        # add it so we don't process this function again if it is called elsewhere
                        included_cfgs.add(callee_name)
                        # extend the callee calls recursively
                        # those functions that where already added
                        # will not be added again
                        callee_cfg_extended = callee_cfg.extended(possible_callees,
                                                                  canvas=canvas,
                                                                  included_cfgs=included_cfgs)

                        # insert the callee at the caller call site
                        canvas.insert_graph_at_node(node, callee_cfg_extended)
                else:
                    # we found a repeating call
                    # this function is already on the canvas graph
                    # just need to hook it up

                    # this is only required to figure out the entry and exit labels of the callee
                    callee_cfg = possible_callees.get(callee_name)

                    canvas.hook_up_call_site(node, callee_cfg.entry_label, callee_cfg.exit_label)

        return canvas

    def hook_up_call_site(self, node, sub_graph_entry, sub_graph_exit):

        parents = self.g.predecessors(node)
        children = self.g.successors(node)

        self.g.remove_node(node)

        # hook it up
        for parent in parents:
            self.g.add_edge(parent, sub_graph_entry)

        for child in children:
            self.g.add_edge(sub_graph_exit, child)

    def insert_graph_at_node(self, node, sub_graph):
        self.g = nx.compose(self.g, sub_graph.g)
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
