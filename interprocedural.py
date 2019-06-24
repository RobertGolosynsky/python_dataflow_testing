from def_use import definition_use_pairs, to_def_use_graph
from cfg import create_cfg, create_super_cfg, to_line_cfg
import networkx as nx
from networkx.drawing.nx_agraph import write_dot, graphviz_layout
import matplotlib.pyplot as plt

class ClassUnderTest(object):
	"""docstring for ClassUnderTest"""
	def __init__(self, arg):
		self.arg = arg
	
	def set(self, an_arg):
		x = 4
		if x>2:
			self.arg = an_arg
		else:
			self.arg = 4

		if self.arg>5:
			print(arg)
		else:
			buf = 33
			self.arg = buf//2
			self.arg = self.arg//2

	def get(self):
		return self.arg




obj = ClassUnderTest(5)
g = create_cfg(obj.set)
pairs = definition_use_pairs(g)



g = create_super_cfg(obj.set, obj.get)
pairs = definition_use_pairs(g)



g = to_def_use_graph(g)
g = to_line_cfg(g)

to_remove = [ (v,u,k,d) for v,u,k,d in g.edges(keys=True, data="varname") if d is not None]
print(to_remove)
g.remove_edges_from(to_remove)

pos = graphviz_layout(g, prog='dot')
nx.draw_networkx_nodes(g, pos, node_size=150, node_color="#ccddff", node_shape="s")

nx.draw_networkx_labels(g, pos, font_size=12, font_color = "black", font_weight="normal")
nx.draw_networkx_edges(g, pos, with_labels=True, arrows=True, node_size=100, edge_color = "black")#, connectionstyle = "arc3,rad=0.5")


collection = nx.draw_networkx_edges(g, pos,with_labels=False, arrows=True, node_size=100, font_size=8, edgelist=to_remove, edge_color = "red", style='dotted', connectionstyle = "arc3,rad=0.5")

for patch in collection:
    patch.set_linestyle('dashed')


edge_labels = { (v,u):(k,d) for v,u,k,d in to_remove}

plt.show()
