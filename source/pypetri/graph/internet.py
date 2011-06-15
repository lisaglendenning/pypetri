# @copyright
# @license

import itertools

import networkx as nx

from .. import trellis

from .. import net
from . import graph

#############################################################################
#############################################################################

class InternetworkGraph(trellis.Component):
    
    Graph = nx.MultiDiGraph

    graphs = trellis.make(tuple)
    graph = trellis.make()
    
    def __init__(self, graphs, g=None, **kwargs):
        if g is None:
            g = self.Graph(**kwargs)
            g = graph.Graph(graph=g)
        super(InternetworkGraph, self).__init__(graphs=graphs,
                                                graph=g,)

    @trellis.maintain(make=dict)
    def edges(self):
        current = self.edges
        new = {}
        graph = self.graph
        graphs = self.graphs
        for g in graphs:
            for vertex in g.vertices.itervalues():
                k = g.graph.name
                for o in vertex.outputs:
                    if o not in g.edges:
                        if o in new:
                            output = new[o][1]
                        else:
                            output = None
                        new[o] = (k, output)
                for i in vertex.inputs:
                    if i not in g.edges:
                        if i in new:
                            input = new[i][0]
                        else:
                            input = None
                        new[i] = (input, k)
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
        graph = self.graph
        graphs = self.graphs
        new = {}
        for g in graphs:
            k = g.graph.name
            if k in new:
                raise ValueError(graphs)
            new[k] = g
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

    def snapshot(self):
        return self.graph.snapshot()
    
#############################################################################
#############################################################################
