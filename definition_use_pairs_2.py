from xdis.std import get_instructions
from xdis import PYTHON_VERSION, IS_PYPY
from control_flow.bb import basic_blocks
from control_flow.cfg import ControlFlowGraph
from control_flow.graph import BB_JUMP_UNCONDITIONAL
from itertools import tee

import dis
import os

from collections import defaultdict

import networkx as nx

label_delimiter = "-"
line_key = "line"
instruction_key = "ins"

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

def get_def(g, node):
	if instruction_key in g.nodes[node]:
		instr = g.nodes[node][instruction_key]
		if instr.opname == "STORE_FAST":
			return instr.argval
		if instr.opname == "STORE_ATTR":
			return "self."+instr.argval

def get_use(g, node):
	if instruction_key in g.nodes[node]:
		instr = g.nodes[node][instruction_key]
		if instr.opname == "LOAD_FAST":
			return instr.argval
		if instr.opname == "LOAD_ATTR":
			return "self."+instr.argval

def has_attr_def(g,node):
	if instruction_key in g.nodes[node]:
		instr = g.nodes[node][instruction_key]
		if instr.opname == "STORE_ATTR":
			return True
	return False

def scope_for(node):
	splitted_label = node.split(label_delimiter)
	if len(splitted_label)>1:
		return splitted_label[0]
	return None

def reaching_definitions(g):
	reach_out = defaultdict(set)
	working_list = set(g.nodes())
	a_node_label = next(iter(working_list))
	is_super_cfg = type(a_node_label) is not int
	
		# is_super_cfg = len().split(label_delimiter) > 1

	while len(working_list) > 0:		
		a_node = working_list.pop()
		old_val = reach_out[a_node]
		reach_in = set()
		for succ in g.predecessors(a_node):
			if is_super_cfg:
				if scope_for(succ) == scope_for(a_node):
					reach_in.update(reach_out[succ])
				else:
					for defining_node in reach_out[succ]:
						if has_attr_def(g, defining_node):
							reach_in.add(defining_node)
			else:
				reach_in.update(reach_out[succ])

		r_out = set()
		if has_def(g, a_node):

			a_node_var = get_def(g, a_node)
			for defining_node in reach_in: 
				if not a_node_var == get_def(g, defining_node): 
					r_out.add(defining_node)

			r_out.add(a_node)

		else:
			r_out = reach_in

		reach_out[a_node] = r_out  
		if not r_out == old_val:
			working_list.update(g.successors(a_node))

	return reach_out


def create_cfg(func):
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
	
	G.name = func.__name__

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


def definition_use_pairs(g):
	pairs = []
	reaching_defs = reaching_definitions(g)
	for node in g:

		if has_use(g, node):

			reach_in = reaching_defs[node]
			for defining_node in reach_in:
				if get_use(g, node) == get_def(g, defining_node):
					pairs.append((defining_node, node))

	return pairs

def line_for_node(g, node):
	return g.nodes[node][line_key] if line_key in g.nodes[node] else node

def ins_for_node(g, node):
	return g.nodes[node][instruction_key] if instruction_key in g.nodes[node] else None

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


def to_def_use_graph(g):
	h = nx.MultiDiGraph(g)
	pairs = definition_use_pairs(h)
	for fr, to in pairs:
		varname = get_def(h, fr)
		h.add_edge(fr, to, def_use = True, key = "def_use", varname=varname)
	return h
