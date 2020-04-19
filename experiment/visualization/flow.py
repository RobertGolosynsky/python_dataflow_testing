import plotly.graph_objects as go
from collections import defaultdict
from collections import Counter
import networkx as nx
from networkx.drawing.nx_pydot import graphviz_layout
import matplotlib.pyplot as plt
from graphs.keys import LINE_KEY
from model.cfg.function_cfg import FunctionCFG
from util.astroid_util import compile_module
import dataflow.reaching_definitions as rd
import graphs.create as gc

colors = [
    '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf',
    'aliceblue', 'antiquewhite', 'aqua', 'aquamarine', 'azure', 'beige', 'bisque', 'black', 'blanchedalmond',
    'blue', 'blueviolet', 'brown', 'burlywood', 'cadetblue', 'chartreuse', 'chocolate', 'coral', 'cornflowerblue',
    'cornsilk', 'crimson', 'cyan', 'darkblue', 'darkcyan', 'darkgoldenrod', 'darkgray', 'darkgrey', 'darkgreen',
    'darkkhaki', 'darkmagenta', 'darkolivegreen', 'darkorange', 'darkorchid', 'darkred', 'darksalmon',
    'darkseagreen', 'darkslateblue', 'darkslategray', 'darkslategrey', 'darkturquoise', 'darkviolet', 'deeppink',
    'deepskyblue', 'dimgray', 'dimgrey', 'dodgerblue', 'firebrick', 'floralwhite', 'forestgreen', 'fuchsia',
    'gainsboro', 'ghostwhite', 'gold', 'goldenrod', 'gray', 'grey', 'green', 'greenyellow', 'honeydew', 'hotpink',
    'indianred', 'indigo', 'ivory', 'khaki', 'lavender', 'lavenderblush', 'lawngreen', 'lemonchiffon',
    'lightblue', 'lightcoral', 'lightcyan', 'lightgoldenrodyellow', 'lightgray', 'lightgrey', 'lightgreen',
    'lightpink', 'lightsalmon', 'lightseagreen', 'lightskyblue', 'lightslategray', 'lightslategrey',
    'lightsteelblue', 'lightyellow', 'lime', 'limegreen', 'linen', 'magenta', 'maroon', 'mediumaquamarine',
    'mediumblue', 'mediumorchid', 'mediumpurple', 'mediumseagreen', 'mediumslateblue', 'mediumspringgreen',
    'mediumturquoise', 'mediumvioletred', 'midnightblue', 'mintcream', 'mistyrose', 'moccasin', 'navajowhite',
    'navy', 'oldlace', 'olive', 'olivedrab', 'orange', 'orangered', 'orchid', 'palegoldenrod', 'palegreen',
    'paleturquoise', 'palevioletred', 'papayawhip', 'peachpuff', 'peru', 'pink', 'plum', 'powderblue', 'purple',
    'red', 'rosybrown', 'royalblue', 'rebeccapurple', 'saddlebrown', 'salmon', 'sandybrown', 'seagreen',
    'seashell', 'sienna', 'silver', 'skyblue', 'slateblue', 'slategray', 'slategrey', 'snow', 'springgreen',
    'steelblue', 'tan', 'teal', 'thistle', 'tomato', 'turquoise', 'violet', 'wheat', 'white', 'whitesmoke',
    'yellow', 'yellowgreen']

# colors = [
#     '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf'
#
# ]
tableau20 = [(31, 119, 180), (174, 199, 232), (255, 127, 14), (255, 187, 120),
             (44, 160, 44), (152, 223, 138), (214, 39, 40), (255, 152, 150),
             (148, 103, 189), (197, 176, 213), (140, 86, 75), (196, 156, 148),
             (227, 119, 194), (247, 182, 210), (127, 127, 127), (199, 199, 199),
             (188, 189, 34), (219, 219, 141), (23, 190, 207), (158, 218, 229)]

colors = list(map(lambda x: "rgba(" + ",".join(map(str, x)) + "," + "0.8)", tableau20))


def color_for(s, d={}):
    print(s)
    print(d)
    if s not in d:
        c = colors[len(d) % len(colors)]
        d[s] = c

    return d[s]
    # return colors[hash(s) % len(colors)]



# fn_name = "_try_fake_instructions_function_arguments"
fn_name = "reaching_definitions"
modd = rd

fns, cls, calls = compile_module(modd.__file__)
rd_func = next(filter(lambda f: f.func.__name__ == fn_name, fns))
cfg = FunctionCFG.create(rd_func)
g: nx.DiGraph = cfg.cfg.g
h = nx.MultiDiGraph()
for fr, to in g.edges():
    f = g.nodes[fr].get(LINE_KEY)
    t = g.nodes[to].get(LINE_KEY)
    if f and t and f != t:
        h.add_edge(f, t)
pairs = list(map(lambda p: (p.definition.line, p.use.line, p.use.varname), cfg.pairs))
paths = defaultdict(list)


def to_edges(p):
    return list(zip(p, p[1:]))


for fr, to, v in pairs:
    for p in nx.all_shortest_paths(h, fr, to):
        edges = to_edges(p)

        paths[v].extend(edges)
l, sc, ds, cc = [], [], [], []
for v, edges in paths.items():
    for (fr, to), c in Counter(edges).items():
        l.append(v)
        sc.append(fr)
        ds.append(to)
        cc.append(c)

ns = list(map(str, range(max(h.nodes) + 1)))
fig = go.Figure(data=[go.Sankey(
    node=dict(
        pad=10,
        thickness=10,
        line=dict(color="black", width=0.5),
        # label=list(map(str, zip(sc,ds))),
        label=ns,
        color="beige"
    ),
    link=dict(
        source=sc,
        target=ds,
        value=cc,
        label=l,
        color=list(map(color_for, l))
    ))])

fig.update_layout(title_text=f"Dataflow of {fn_name}", font_size=10)
fig.show()
