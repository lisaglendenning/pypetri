"""
Requires pygraphviz
"""

import networkx as nx

SHAPE = 'shape'
SHAPES = { 'conditions': 'ellipse', 
           'transitions': 'box',
         }

def markup(network, graph=None, shapes=None):
    if shapes is None:
        shapes = SHAPES
    if graph is None:
        graph = network.graph.snapshot()
    for u in graph:
        v = network.vertices[u]
        for k in shapes:
            role = getattr(network.network, k)
            if v in role:
                graph.node[u][SHAPE] = shapes[k]
    return graph

def write(graph, filename=None):
    if filename is None:
        filename = '%s.dot' % graph.name
    nx.write_dot(graph, filename)
