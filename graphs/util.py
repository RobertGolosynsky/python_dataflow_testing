def node_where(g, attribute_name, attribute_value):
    for node, data in g.nodes(data=True):
        if attribute_name in data and data[attribute_name] == attribute_value:
            return node, data
    return None, None


def nodes_with_out_degree(g, degree):
    return [node for node, out_degree in g.out_degree if out_degree == degree]


def nodes_with_in_degree(g, degree):
    return [node for node, in_degree in g.in_degree if in_degree == degree]
