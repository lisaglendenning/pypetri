# @copyright
# @license

import itertools

import networkx as nx

from .. import trellis

from .. import net
from . import graph

#############################################################################
#############################################################################

class NetworkGraph(trellis.Component):

    Graph = nx.MultiDiGraph
    
    toname = trellis.make()
    network = trellis.make()
    graph = trellis.make()
    
    def __init__(self, network, toname, g=None, **kwargs):
        if g is None:
            if 'name' not in kwargs:
                kwargs['name'] = toname(network) 
            g = self.Graph(**kwargs)
            g = graph.Graph(graph=g)
        super(NetworkGraph, self).__init__(network=network, 
                                           toname=toname, 
                                           graph=g,)

    @trellis.maintain(make=dict)
    def edges(self):
        current = self.edges
        new = {}
        toname = self.toname
        vertices = self.vertices
        graph = self.graph
        for node,vertex in vertices.iteritems():
            for o in vertex.outputs:
                output = toname(o.output)
                if output in vertices:
                    edge = (node, output)
                    new[o] = edge
        removed = [k for k in current if k not in new or current[k] is not new[k]]
        for k in removed:
            edge = current[k]
            graph.remove_edge(*edge, key=id(k))
            del current[k]
        added = [k for k in new if k not in current]
        for k in added:
            edge = new[k]
            current[k] = edge
            graph.add_edge(*edge, key=id(k))
        if added or removed:
            trellis.mark_dirty()
        return current
        
    @trellis.maintain(make=dict)
    def vertices(self):
        network = self.network
        graph = self.graph
        toname = self.toname
        new = dict([(toname(v), v) for v in itertools.chain(network.conditions, network.transitions)])
        current = self.vertices
        removed = [k for k in current if k not in new or current[k] is not new[k]]
        for k in removed:
            graph.remove_node(k)
            del current[k]
        added = [k for k in new if k not in current]
        for k in added:
            v = new[k]
            current[k] = v
            role = 'condition' if v in network.conditions else 'transition'
            graph.add_node(k, role=role)
        if added or removed:
            trellis.mark_dirty()
        return current
    
    @trellis.compute
    def snapshot(self):
        return self.graph.snapshot

#############################################################################
#############################################################################
