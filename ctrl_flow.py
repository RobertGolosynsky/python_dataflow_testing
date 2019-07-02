from xdis.std import get_instructions
from xdis import PYTHON_VERSION, IS_PYPY
from control_flow.bb import basic_blocks
from control_flow.cfg import ControlFlowGraph
from control_flow.graph import BB_JUMP_UNCONDITIONAL

import networkx as nx

from collections import defaultdict
from util import pairwise

label_delimiter = "-"
line_key = "line"
instruction_key = "ins"
instructions_key = "instrs"
scope_key = "scope"


def line_for_node(g, node):
	return g.nodes[node][line_key] if line_key in g.nodes[node] else node


def ins_for_node(g, node):
	return g.nodes[node][instruction_key] if instruction_key in g.nodes[node] else None


def instructions_for_node(g, node):
	return g.nodes[node][instructions_key] if instructions_key in g.nodes[node] else []


def create_cfg(func, name=None):
	bb_mgr = basic_blocks(PYTHON_VERSION, IS_PYPY, func)

	cfg = ControlFlowGraph(bb_mgr)
	g = cfg.graph

	G = nx.MultiDiGraph()
	
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
					G.add_edge(source, offset)
					source = offset

	for edge in g.edges:
			if edge.kind == 'fallthrough' \
					and \
					BB_JUMP_UNCONDITIONAL in edge.source.flags:
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


def merge_cfgs(cfgs, scopes):

	for cfg, scope in zip(cfgs, scopes):
		# for node in cfg:
		nx.set_node_attributes(cfg, scope, scope_key)
			# cfg[node][scope_key] = scope
		# print(cfg.nodes(data=True))

	g = nx.union_all(cfgs)#, rename=scopes)

	for (cfg1, scope1), (cfg2, scope2) in pairwise(zip(cfgs, scopes)):
		entry = next(iter(sorted(cfg2.in_degree, key=lambda x: x[1])))[0]
		exit = next(iter(sorted(cfg1.out_degree, key=lambda x: x[1])))[0]
		# g.add_edge(scope1+exit, scope2+entry)
		g.add_edge(exit, entry)
	return g


def create_super_cfg_from_cfgs(*cfgs):
	prefixes = tuple([str(i) + label_delimiter for i in range(len(cfgs))])
	g = nx.union_all(list(cfgs), rename=prefixes)
	for (cfg1, prefix1), (cfg2, prefix2) in pairwise(zip(cfgs, prefixes)):
		entry = next(iter(sorted(cfg2.in_degree, key=lambda x: x[1])))[0]
		exit = next(iter(sorted(g.out_degree, key=lambda x: x[1])))[0]

		# max_node = sorted(cfg1.nodes())[-	1]
		# if entry == 40:
		# 	x = nx.union(cfg2, to_line_cfg(cfg2), rename=("b", "l"))
		# 	pos = graphviz_layout(x, prog='dot')
		# 	# labels = {l: str(l[-2:]) for l in one.nodes}
		# 	# print(labels)
		# 	for node, data in cfg2.nodes(data=True):
		# 		print(node, data[instruction_key] if instruction_key in data else None)
		#
		# 	nx.draw_networkx(x, pos, node_size=150, node_color="#ccddff", node_shape="s")
		# 	# nx.draw_networkx_edges(one, pos, edgelist=pairs)
		#
		# 	plt.show()
		# print(entry)
		g.add_edge(exit, prefix2 + entry)

	return g


def create_super_cfg(*funcs):
	return create_super_cfg_from_cfgs([create_cfg(f) for f in funcs])


def to_line_cfg(g):
	h = nx.MultiDiGraph()
	lines = defaultdict(list)
	for node in g.nodes():
		instr = ins_for_node(g, node)
		if instr:
			lines[line_for_node(g, node)].append(instr)

	for line_num in lines:
		args = {instructions_key:lines[line_num]}
		h.add_node(line_num, **args)

	for fr, to, key in g.edges(keys=True):
		line_from = line_for_node(g, fr)
		line_to = line_for_node(g, to)
		h.add_edge(line_from, line_to, key=key, **g.edges[fr,to,key])
	return h
