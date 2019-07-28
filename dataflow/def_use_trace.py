# from collections import defaultdict
#
#
# def _reaching_definitions(trace):
#     reach_out = defaultdict(set)
#     for el in trace:
#         a_node = working_list.pop()
#         # print(a_node)
#         old_val = reach_out[a_node]
#         # print("before ", old_val)
#         node_reach_in = set()
#         if initial_set:
#             node_reach_in = initial_set.get(a_node, set())
#         for a_pred in cfg.predecessors(a_node):
#             node_reach_in.update(reach_out[a_pred])
#
#         node_reach_out = set()
#         node_attrs: dict = cfg.nodes[a_node]
#         node_definition = node_attrs.get(du.DEFINITION_KEY, None)
#         node_file = node_attrs.get(du.FILE_KEY, "UNDEFINED")
#         node_line = node_attrs.get(cr.LINE_KEY, -1)
#         if node_definition:
#             for reaching_var in node_reach_in:
#                 if not reaching_var.varname == node_definition:
#                     node_reach_out.add(reaching_var)
#             if not initial_set:
#                 defined_var = Var(node_file, node_line, node_definition)
#                 node_reach_out.add(defined_var)
#         else:
#             node_reach_out = node_reach_in
#
#         reach_out[a_node] = node_reach_out
#         # print("after ", node_reach_out)
#         if not node_reach_out == old_val:
#             working_list.update(cfg.successors(a_node))
#
#     return reach_out
#