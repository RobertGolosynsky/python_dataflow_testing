from xdis.std import get_instructions
from xdis import PYTHON_VERSION, IS_PYPY
from control_flow.bb import basic_blocks
from control_flow.cfg import ControlFlowGraph
from control_flow.graph import BB_JUMP_UNCONDITIONAL
from itertools import tee

import dis
import os

import networkx as nx

from collections import defaultdict


label_delimiter = "-"
line_key = "line"
instruction_key = "ins"


def line_for_node(g, node):
	return g.nodes[node][line_key] if line_key in g.nodes[node] else node


def ins_for_node(g, node):
	return g.nodes[node][instruction_key] if instruction_key in g.nodes[node] else None


def create_cfg(func, name=None):
	bb_mgr = basic_blocks(PYTHON_VERSION, IS_PYPY, func)

	cfg = ControlFlowGraph(bb_mgr)
	g = cfg.graph

	G = nx.DiGraph()
	
	instructions = list(get_instructions(func))

	offset_to_instruction = {}

	for i in instructions:
		offset_to_instruction[i.offset]=i

	offset_to_line = {}

	for i in instructions:
		offset = i.offset 
		instr = i
		while not instr.starts_line:
			offset-=2
			instr = offset_to_instruction[offset]
		offset_to_line[i.offset]=instr.starts_line


	for instr in instructions:
		attrs = {}
		attrs[line_key] = str(offset_to_line[instr.offset])
		attrs[instruction_key] = instr
		G.add_node(instr.offset, **attrs)

	for node in g.nodes: 
		start = node.bb.index[0]
		end = node.bb.index[1]

		source = start
		for offset in range(start+2, end+2, 2):
			for ins in instructions: 
				if ins.offset == offset:
					G.add_edge(source,offset)
					source = offset

	for edge in g.edges:
			if (edge.kind == 'fallthrough' and BB_JUMP_UNCONDITIONAL in edge.source.flags):
				continue
			source = edge.source 
			dest = edge.dest
			source_offset = source.bb.index[1]
			dest_offset = dest.bb.index[0]

			G.add_edge(source_offset, dest_offset)

	entry = next(iter(sorted(G.in_degree, key=lambda x: x[1])))[0]
	exit = next(iter(sorted(G.out_degree, key=lambda x: x[1])))[0]
	
	G.name = func.__name__ if not name else name

	G.add_edge("Entry {}".format(G.name), entry)

	G = nx.relabel_nodes(G, {exit:"Exit {}".format(G.name)}, copy=False)
	return G


def pairwise(iterable):
    "s -> (s0,s1), (s1,s2), (s2, s3), ..."
    a, b = tee(iterable)
    next(b, None)
    return zip(a, b)

def create_super_cfg(*funcs):
	cfgs = [create_cfg(f) for f in funcs]
	prefixes = tuple([str(i)+label_delimiter for i in range(len(funcs))])
	g = nx.union_all(cfgs, rename=prefixes)
	for (cfg1, prefix1), (cfg2, prefix2) in pairwise(zip(cfgs, prefixes)):
		entry = next(iter(sorted(cfg2.in_degree, key=lambda x: x[1])))[0]
		exit = next(iter(sorted(g.out_degree, key=lambda x: x[1])))[0]
		
		# max_node = sorted(cfg1.nodes())[-	1]
		g.add_edge(exit, prefix2+entry)

	return g


def to_line_cfg(g):
	h = nx.MultiDiGraph()
	lines = defaultdict(list)
	for node in g.nodes():
		lines[line_for_node(g, node)].append(ins_for_node(g, node))

	for line_num in lines:
		h.add_node(line_num, instrs = lines[line_num])

	for fr, to, key in g.edges(keys=True):
		line_from = line_for_node(g, fr)
		line_to = line_for_node(g, to)
		h.add_edge(line_from, line_to, key=key, **g.edges[fr,to,key])
	return h
