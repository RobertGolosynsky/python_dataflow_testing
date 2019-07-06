def node_where(g, attribute_name, attribute_value):
    for node, data in g.nodes(data=True):
        if attribute_name in data and data[attribute_name] == attribute_value:
            return node, data
    return None, None
