"""
Requires pygraphviz
"""

import networkx as nx

from ..net import *

SHAPE = 'shape'
SHAPES = { 'conditions': 'ellipse', 
           'transitions': 'box',
           'network': 'doubleoctagon',
         }

def markup(network, graph=None, shapes=None):
    if shapes is None:
        shapes = SHAPES
    if graph is None:
        graph = network.snapshot()
    for u in graph:
        v = network.vertices[u]
        if isinstance(network, NetworkGraph):
            for k in 'conditions', 'transitions',:
                role = getattr(network.network, k)
                if v in role:
                    break
        else:
            k = 'network'
        graph.node[u][SHAPE] = shapes[k]
    return graph

def write(graph, filename=None):
    if filename is None:
        filename = '%s.dot' % graph.name
    nx.write_dot(graph, filename)
