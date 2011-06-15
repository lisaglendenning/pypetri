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
    
    Arc = net.Arc
    Vertex = net.Vertex
    Network = net.Network

    Graph = nx.MultiDiGraph
    
    toname = trellis.make()
    network = trellis.make()
    graph = trellis.make()
    
    def __init__(self, network, toname, g=None, **kwargs):
        if g is None:
            g = self.Graph(name=toname(network), **kwargs)
            g = graph.Graph(graph=g)
        super(NetworkGraph, self).__init__(network=network, 
                                           toname=toname, 
                                           graph=g, **kwargs)

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
        removed = [k for k in current if k not in new or current[k] != new[k]]
        if removed:
            graph.remove_edges_from([current[k] for k in removed])
            for k in removed:
                del current[k]
        added = [k for k in new if k not in current]
        if added:
            current.update([(k, new[k]) for k in added])
            graph.add_edges_from([current[k] for k in added])
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
        removed = [k for k in current if k not in new or current[k] != new[k]]
        if removed:
            graph.remove_nodes_from(removed)
            for k in removed:
                del current[k]
        added = [k for k in new if k not in current]
        if added:
            current.update([(k, new[k]) for k in added])
            graph.add_nodes_from(added)
        if added or removed:
            trellis.mark_dirty()
        return current

#############################################################################
#############################################################################
