# @copyright
# @license

import networkx as nx

import pypetri.trellis as trellis

import pypetri.net as pnet
import pypetri.graph.graph as pgraph

#############################################################################
#############################################################################

class NetworkGraph(trellis.Component):

    Graph = nx.MultiDiGraph
    
    net = trellis.attr(None)
    graph = trellis.attr(None)
    
    ROLES = 'arc', 'transition', 'condition', 'network',
    ARC, TRANSITION, CONDITION, NETWORK, = ROLES
    LABELS = 'name', 'role', 'subgraph'
    NAME, ROLE, SUBGRAPH, = LABELS
    
    def __init__(self, net, graph=None, *args, **kwargs):
        if graph is None:
            graph = self.Graph(*args, name=net.name, **kwargs)
            graph = pgraph.Graph(graph=graph)
        super(NetworkGraph, self).__init__(net=net, graph=graph)
    
    
    @trellis.maintain
    def subgraphs(self):
        if self.net is None or self.net.networks is None:
            return {}
        current = set(self.subgraphs.values()) if self.subgraphs is not None else set()
        updated = self.net.networks
        new = {}
        for net in updated:
            if net.name in current:
                subgraph = current[net.name]
            else:
                subgraph = self.__class__(net)
            new[net.name] = subgraph
        return new
    
    @trellis.maintain
    def edges(self):
        if self.net is None or self.net.arcs is None:
            return set()
        current = self.edges if self.edges is not None else set()
        new = set()
        for arc in self.net.arcs:
            nodes = [arc.source, arc.sink]
            if None in nodes:
                continue
            for i in xrange(len(nodes)):
                while nodes[i].domain is not self.net:
                    assert nodes[i].domain is not None
                    nodes[i] = nodes[i].domain
            nodes = tuple([n.name for n in nodes])
            attrs = {self.ROLE: self.ARC, self.NAME: arc.name, }
            if nodes not in current:
                if nodes[0] not in self.graph or nodes[1] not in self.graph:
                    continue
                self.graph.add_edge(*nodes, **attrs)
            else:
                if self.graph.edge[nodes[0]][nodes[1]] != attrs:
                    self.graph.edge[nodes[0]][nodes[1]].update(attrs)
            new.add(nodes)
        removed = current - new
        self.graph.remove_edges_from(removed)
        return new
        
    @trellis.maintain
    def vertices(self):
        if self.net is None or None in (self.net.transitions, self.net.conditions, self.net.networks,):
            return set()
        current = self.vertices if self.vertices is not None else set()
        new = set()
        for vertices, label in ((self.net.transitions, self.TRANSITION),
                                (self.net.conditions, self.CONDITION),
                                (self.net.networks, self.NETWORK),):
            for vertex in vertices:
                vertex = vertex.name
                attrs = {self.ROLE: label, self.NAME: vertex, }
                if vertex not in current:
                    self.graph.add_node(vertex, **attrs)
                else:
                    if self.graph.node[vertex] != attrs:
                        self.graph.node[vertex].update(attrs)
                new.add(vertex)
        removed = current - new
        self.graph.remove_nodes_from(removed)
        return new
                      
    def snapshot(self):
        graph = self.graph.snapshot()
        
        for name, sub in self.subgraphs.iteritems():
            subgraph = sub.snapshot()
            graph.node[name][self.SUBGRAPH] = subgraph
        
        return graph


#############################################################################
#############################################################################
