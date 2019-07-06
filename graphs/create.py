import inspect

from xdis.std import get_instructions, Instruction
from xdis import PYTHON_VERSION, IS_PYPY
from control_flow.bb import basic_blocks
from control_flow.cfg import ControlFlowGraph
from control_flow.graph import BB_JUMP_UNCONDITIONAL

import networkx as nx

from collections import defaultdict, namedtuple

label_delimiter = "-"
line_key = "line"
instruction_key = "ins"
instructions_key = "instrs"
scope_key = "scope"

FakeBytecodeInstruction = namedtuple("FakeBytecodeInstruction", ["offset", "opname", "argval", "starts_line"])


def _line_for_node(g, node):
    return g.nodes[node][line_key] if line_key in g.nodes[node] else None


def _ins_for_node(g, node):
    return g.nodes[node][instruction_key] if instruction_key in g.nodes[node] else None


def _instructions_for_node(g, node):
    return g.nodes[node][instructions_key] if instructions_key in g.nodes[node] else None


def create_cfg(func):
    offset_wise_cfg = _create_byte_offset_cfg(func)
    if not offset_wise_cfg:
        return None

    line_wise_cfg = _as_line_wise_cfg(offset_wise_cfg)

    return line_wise_cfg


def _as_line_wise_cfg(g):
    h = nx.DiGraph()
    lines = defaultdict(list)
    for node in g.nodes():
        instr = _ins_for_node(g, node)
        if instr:
            lines[_line_for_node(g, node)].append(instr)

    for line_num in lines:
        args = {
            instructions_key: _instructions_as_graph(lines[line_num])
        }
        h.add_node(line_num, **args)

    for fr, to in g.edges():
        line_from = _line_for_node(g, fr)
        line_to = _line_for_node(g, to)
        h.add_edge(line_from, line_to)
    h = _add_entry_and_exit_nodes(h, "Entry", "Exit")
    nx.relabel_nodes(h, mapping={l: str(l) for l in h.nodes()}, copy=False)
    return h


def _get_instructions(func):
    instrs = []
    for ins in get_instructions(func):
        argval = None
        if isinstance(ins.argval, str):
            argval = ins.argval
        fake = FakeBytecodeInstruction(ins.offset, ins.opname, argval, ins.starts_line)
        instrs.append(fake)
    return instrs


def _create_byte_offset_cfg(func):
    try:
        bb_mgr = basic_blocks(PYTHON_VERSION, IS_PYPY, func)
    except:
        return None
    cfg = ControlFlowGraph(bb_mgr)
    byte_blocks_graph = cfg.graph

    g = nx.MultiDiGraph()

    instructions = list(_get_instructions(func))

    fake_instructions = _fake_instructions_function_arguments(func)
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
            line_key: offset_to_line[instr.offset],
            instruction_key: instr
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
        if edge.kind == 'fallthrough' \
                and \
                BB_JUMP_UNCONDITIONAL in edge.source.flags:
            continue
        source = edge.source
        dest = edge.dest
        source_offset = source.bb.index[1]
        dest_offset = dest.bb.index[0]
        if dest_offset % 2 == 0: # don't add an extra node for exit
            g.add_edge(source_offset, dest_offset)

    if len(fake_instructions) > 0:
        fake_instructions = list(sorted(fake_instructions, key=lambda i: i.offset))

        for i1, i2 in zip(fake_instructions, fake_instructions[1:]):
            g.add_edge(i1.offset, i2.offset)

        last_fake_instruction_offset = fake_instructions[-1].offset
        first_real_instruction_offset = 0

        g.add_edge(last_fake_instruction_offset, first_real_instruction_offset)
    nx.relabel_nodes(g, mapping={l: str(l) for l in g.nodes()}, copy = False)

    return g


def _fake_instructions_function_arguments(func):
    _, function_definition_line = inspect.getsourcelines(func)
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
            fake_offset = -2 - i*2
            fake_instruction = FakeBytecodeInstruction(fake_offset, "STORE_FAST", arg, False)
            instructions.append(fake_instruction)
            max_offset = fake_offset
    if len(args) > 0:
        instruction_with_line = FakeBytecodeInstruction(
            max_offset-2,
            "STORE_FAST",
            args[0],
            function_definition_line
        )
        instructions.append(instruction_with_line)

    return instructions


def _instructions_as_graph(instructions):
    g = nx.DiGraph()
    for ins in instructions:
        g.add_node(ins.offset, **{instruction_key:ins})

    for ins1, ins2 in zip(instructions, instructions[1:]):
        g.add_edge(ins1.offset, ins2.offset)
    nx.relabel_nodes(g, mapping={l: str(l) for l in g.nodes()}, copy=False)
    return g


def _add_entry_and_exit_nodes(g, entry_label, exit_label):
    entry_node = next(iter(sorted(g.in_degree, key=lambda x: x[1])))[0]
    exit_node = next(iter(sorted(g.out_degree, key=lambda x: x[1])))[0]

    g.add_edge(entry_label, entry_node)

    # nx.relabel_nodes(g, {exit_node: exit_label}, copy=False)

    g.add_edge(exit_node, exit_label)
    return g
