# @copyright
# @license

import networkx as nx

from .. import trellis

from .. import net
from . import graph

#############################################################################
#############################################################################

class GraphNetwork(trellis.Component):
    r"""Petri net components must have a unique string value."""
    
    Arc = net.Arc
    Vertex = net.Vertex
    Network = net.Network

    Graph = nx.MultiDiGraph
    
    net = trellis.make(None)
    graph = trellis.make(None)
    
    def __init__(self, net, g=None, *args, **kwargs):
        if g is None:
            g = self.Graph(*args, name=str(net), **kwargs)
            g = graph.Graph(graph=g)
        super(GraphNetwork, self).__init__(*args, net=net, graph=g, **kwargs)
    
    def find(self, node):
        if node in self.vertices:
            return self.vertices[node]
        for subgraph in self.subgraphs.itervalues():
            v = subgraph.find(node)
            if v is not None:
                return v
        return None
    
    @trellis.maintain
    def subgraphs(self):
        if self.net is None or not self.vertices:
            return {}
        vertices = self.vertices
        current = self.subgraphs if self.subgraphs is not None else {}
        removed = [k for k in current if k not in vertices or vertices[k] is not current[k]]
        for k in removed:
            del current[k]
        for k,v in vertices.iteritems():
            if k in current or not isinstance(v, self.Network):
                continue
            subgraph = self.__class__(v)
            current[k] = subgraph
        return current
    
    @trellis.maintain
    def edges(self):
        if self.net is None or not self.net.arcs:
            self.graph.remove_edges_from(self.graph.edges())
            return {}
        arcs = self.net.arcs
        current = self.edges if self.edges is not None else {}
        new = {}
        for arc in arcs:
            vertices = [None, None]
            for i,v in enumerate((arc.input, arc.output,)):
                while v is not None:
                    if isinstance(v, self.Vertex):
                        break
                    v = v.input
                if v is not None:
                    node = str(v)
                    if node not in self.vertices:
                        for subgraph in self.subgraphs.itervalues():
                            if subgraph.find(node) is not None:
                                v = subgraph
                                break
                        else:
                            v = None
                if v is None:
                    break
                vertices[i] = str(v)
            else:
                vertices = tuple(vertices)
                edge = str(arc)
                new[edge] = vertices
        removed = [k for k in current if k not in new or current[k] != new[k]]
        self.graph.remove_edges_from([current[k] for k in removed])
        for k in removed:
            del current[k]
        for k,v in new.iteritems():
            if k not in current or v != current[k]:
                for u in v:
                    if u not in self.vertices:
                        break
                else:
                    self.graph.add_edge(*v)
                    current[k] = v
        return current
        
    @trellis.maintain
    def vertices(self):
        if self.net is None or not self.net.vertices:
            self.graph.remove_nodes_from(self.graph.nodes())
            return {}
        vertices = self.net.vertices
        current = self.vertices if self.vertices is not None else {}
        removed = [k for k,v in current.iteritems() if v not in vertices]
        self.graph.remove_nodes_from(removed)
        for k in removed:
            del current[k]
        for v in vertices:
            node = str(v)
            if node not in current:
                current[node] = v
                self.graph.add_node(node)
        trellis.mark_dirty()
        return current
                      
    def snapshot(self, flatten=True):
        g = self.graph.snapshot()
        
        if flatten:
            subgraphs = {}
            for name, subgraph in self.subgraphs.iteritems():
                subgraphs[name] = subgraph.snapshot(flatten)
            
            for name, subgraph in subgraphs.iteritems():
                # add nodes
                for u in subgraph:
                    if u in g:
                        raise ValueError("non-unique node name: %s" % u)
                    g.add_node(u) 
                    
                # add edges
                g.add_edges_from(subgraph.edges_iter())
                
                # replace edges to subgraph
                for arc in self.net.arcs:
                    edge = self.edges[str(arc)]
                    if name not in edge:
                        continue
                    vertices = [str(u) for u in (arc.input, arc.output,)]
                    edge = [x if x in g else y for x,y in zip(vertices, edge)]
                    g.add_edge(*edge)
                g.remove_node(name)
        return g


#############################################################################
#############################################################################
