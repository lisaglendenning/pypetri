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
    
    net = trellis.make(None)
    
    def __init__(self, net, graph=None, *args, **kwargs):
        if graph is None:
            graph = self.Graph(*args, name=net.name, **kwargs)
            graph = pgraph.Graph(graph=graph)
        super(NetworkGraph, self).__init__(net=net)
        self.graph = graph
        self.subgraphs = trellis.Dict()
    
    @trellis.maintain
    def recurse(self):
        nets = set([k for k in self.net if isinstance(self.net[k], pnet.Network)])
        graphs = set(self.subgraphs.keys())
        added = nets - graphs
        removed = graphs - nets
        for u in added:
            v = self.net[u]
            self.subgraphs[u] = self.__class__(v)
        for u in removed:
            del self.subgraphs[u]

    @trellis.maintain
    def associate(self):
        arcs = set()
        vertices = set()
        for u,v in self.net.iteritems():
            if isinstance(v, self.net.Arc):
                arcs.add(u)
            else:
                vertices.add(u)
                
        has = set(self.graph.nodes())
        added = vertices - has
        removed = has - vertices
        self.graph.add_nodes_from(added)
        self.graph.remove_nodes_from(removed)
        
        edges = set()
        for u in arcs:
            arc = self.net[u]
            nodes = [arc.source, arc.sink]
            if None in nodes:
                continue
            for i in xrange(len(nodes)):
                while nodes[i].domain is not self.net:
                    assert nodes[i].domain is not None
                    nodes[i] = nodes[i].domain
                assert (nodes[i].name in self.graph) or (nodes[i].name in added)
            edges.add((nodes[0].name, nodes[1].name,))

        has = set(self.graph.edges()) 
        added = edges - has
        removed = has - edges
        self.graph.add_edges_from(added)
        self.graph.remove_edges_from(removed)
                      
    def snapshot(self):
        graph = self.graph.snapshot()
        
        subgraphs = {}
        for name, sub in self.subgraphs.iteritems():
            subgraphs[name] = sub.snapshot()
        
        return graph, subgraphs


#############################################################################
#############################################################################
