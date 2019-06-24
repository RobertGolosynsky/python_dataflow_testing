from collections import defaultdict
from cfg import instruction_key, line_key, label_delimiter
import networkx as nx


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


def to_def_use_graph(g):
	h = nx.MultiDiGraph(g)
	pairs = definition_use_pairs(h)
	for fr, to in pairs:
		varname = get_def(h, fr)
		h.add_edge(fr, to, def_use = True, key = "def_use", varname=varname)
	return h
