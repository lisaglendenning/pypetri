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
        for k,subgraph in self.vertices.iteritems():
            for vertex in subgraph.vertices.itervalues():
                for o in vertex.outputs:
                    if o not in subgraph.edges:
                        if o in new:
                            output = new[o][1]
                        else:
                            output = None
                        new[o] = (k, output)
                for i in vertex.inputs:
                    if i not in subgraph.edges:
                        if i in new:
                            input = new[i][0]
                        else:
                            input = None
                        new[i] = (input, k)
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
        graph = self.graph
        graphs = self.graphs
        new = {}
        for g in graphs:
            k = g.graph.name
            if k in new:
                raise ValueError(graphs)
            new[k] = g
        current = self.vertices
        removed = [k for k in current if k not in new or current[k] is not new[k]]
        for k in removed:
            graph.remove_node(k)
            del current[k]
        added = [k for k in new if k not in current]
        for k in added:
            v = new[k]
            current[k] = v
            role = 'network'
            graph.add_node(k, role=role)
        if added or removed:
            trellis.mark_dirty()
        return current

    def snapshot(self, flatten=False, toname=lambda g,v: '.'.join((g,v)) if g else v):
        g = self.graph.snapshot()
        if not flatten:
            return g
        # add intranetwork vertices
        vertices = {}
        for k, subgraph in self.vertices.iteritems():
            for node in subgraph.graph.nodes_iter(data=True):
                pair = (k, node[0])
                v = toname(*pair)
                if v in vertices or v in g:
                    raise ValueError(v)
                vertices[v] = pair
                g.add_node(v, **node[1])
        # add intranetwork edges
        for k, subgraph in self.vertices.iteritems():
            for edge in subgraph.graph.edges_iter(data=True, keys=True):
                u,v,a,d = edge
                u,v = toname(k, u), toname(k, v)
                g.add_edge(u, v, key=a, **d)
        # add internetwork edges
        for arc, edge in self.edges.iteritems():
            u, v = arc.input, arc.output
            input, output = edge
            subgraph = self.vertices[input]
            u = toname(input, subgraph.toname(u))
            assert u in g
            subgraph = self.vertices[output]
            v = toname(output, subgraph.toname(v))
            assert v in g
            k = id(arc)
            d = g.edge[edge[0]][edge[1]][k]
            g.add_edge(u, v, key=k, **d)
        # remove aggregated vertices/edges
        g.remove_nodes_from(self.vertices.keys())
        return g
    
    
#############################################################################
#############################################################################
