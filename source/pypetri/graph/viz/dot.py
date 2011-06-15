"""
Requires pygraphviz
"""

import networkx as nx
import pygraphviz as pgv

from ..net import *

SHAPE = 'shape'
SHAPES = { 'condition': 'ellipse', 
           'transition': 'box',
           'network': 'doubleoctagon',
         }

def markup(graph, label=None, overlap=False, shapes=SHAPES):
    g = nx.to_agraph(graph)
    graph_attr = dict()
    if label is None:
        label = graph.name
    graph_attr['label'] = label
    graph_attr['overlap'] = 'true' if overlap else 'false'
    for k,v in graph_attr.iteritems():
        g.graph_attr[k] = v
    for u in graph:
        role = graph.node[u]['role']
        n = g.get_node(u)
        n.attr[SHAPE] = shapes[role]
    return g

def write(graph, filename=None):
    if filename is None:
        filename = '%s.dot' % graph.name
    graph.write(filename)

def draw(graph, filename=None, format='png', layout='neato'):
    if filename is None:
        filename = graph.name
    graph.draw("%s.%s" % (filename, format), prog=layout)
