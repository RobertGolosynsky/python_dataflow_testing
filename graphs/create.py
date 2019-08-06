import inspect

from xdis.std import get_instructions, Instruction
from xdis import PYTHON_VERSION, IS_PYPY
from control_flow.bb import basic_blocks
from control_flow.cfg import ControlFlowGraph
from control_flow.graph import BB_JUMP_UNCONDITIONAL, FLAG2NAME, \
    BB_NOFOLLOW, BB_END_FINALLY, BB_FINALLY, BB_STARTS_POP_BLOCK

import networkx as nx
from loguru import logger

from collections import namedtuple
import graphs.util as gu

LINE_KEY = "line"
INSTRUCTION_KEY = "ins"
FILE_KEY = "file"

FakeBytecodeInstruction = namedtuple("FakeBytecodeInstruction", ["offset", "opname", "argval", "starts_line"])

exit_node_offset = 1


def try_create_cfg(func, definition_line=None, args=None):
    offset_wise_cfg = _try_create_byte_offset_cfg(func, definition_line=definition_line, args=args)
    if not offset_wise_cfg:
        return None
    # if not file_path:
    #     file_path = inspect.getfile(func)
    # nx.set_node_attributes(offset_wise_cfg, file_path, name=FILE_KEY)
    return offset_wise_cfg


def _get_instructions(func, definition_line=None):
    instrs = []
    for ins in get_instructions(func, first_line=None):
        argval = None
        if isinstance(ins.argval, str) or isinstance(ins.argval, int):
            argval = ins.argval
        fake = FakeBytecodeInstruction(ins.offset, ins.opname, argval, ins.starts_line)
        instrs.append(fake)
    return instrs


def _try_create_byte_offset_cfg(func, definition_line=None, args=None):
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

    if len(fake_instructions) > 0:
        fake_instructions = list(sorted(fake_instructions, key=lambda i: i.offset))

        for i1, i2 in zip(fake_instructions, fake_instructions[1:]):
            g.add_edge(i1.offset, i2.offset)

        last_fake_instruction_offset = fake_instructions[-1].offset
        first_real_instruction_offset = 0

        g.add_edge(last_fake_instruction_offset, first_real_instruction_offset)
    nx.relabel_nodes(g, mapping={l: str(l) for l in g.nodes()}, copy=False)
    return g


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


def _add_entry_and_exit_nodes(g, entry_label, exit_label):
    # exit already added, but not for try blocks and other hanging code
    entry_nodes = gu.nodes_with_in_degree(g, 0)
    # gd.draw_line_cfg(g)
    # assert len(entry_nodes) == 1

    entry_node = entry_nodes[0]

    exit_nodes = gu.nodes_with_out_degree(g, 0)

    for exit_node in exit_nodes:
        if not exit_node == exit_label:
            g.add_edge(exit_node, exit_label)

    g.add_edge(entry_label, entry_node)

    return g


def _line_for_node(g, node):
    return g.nodes[node][LINE_KEY] if LINE_KEY in g.nodes[node] else None


def _ins_for_node(g, node):
    return g.nodes[node][INSTRUCTION_KEY] if INSTRUCTION_KEY in g.nodes[node] else None
