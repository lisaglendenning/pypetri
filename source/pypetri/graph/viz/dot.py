
def dot(graph, network):
    for u in graph:
        v = network.find(u)
        if isinstance(v, network.Condition):
            shape = 'ellipse'
        elif isinstance(v, network.Transition):
            shape = 'box'
        else:
            shape = 'doubleoctagon'
        graph.node[u]['shape'] = shape

    return graph
