
import pypetri.trellis as trellis

import pypetri.hub as phub
import pypetri.graph.graph as pgraph

#############################################################################
#############################################################################

class HubGraph(trellis.Component):
    
    hub = trellis.make(None)
    graph = trellis.make(None)
    
    Graph = pgraph.Graph
    
    def __init__(self, hub, graph=None, *args, **kwargs):
        if graph is None:
            graph = self.Graph(*args, **kwargs)
        super(HubGraph, self).__init__(hub=hub)
        self.graph = graph
        self.subgraphs = trellis.Dict()
    
    name = property(lambda self: self.hub.name)
    inferiors = property(lambda self: self.hub.inferiors)
    
    @trellis.maintain
    def recurse(self):
        hubs = set([k for k,v in self.inferiors.iteritems() if isinstance(v, phub.Hub)])
        graphs = set(self.subgraphs.keys())
        added = hubs - graphs
        removed = graphs - hubs
        for u in added:
            v = self.inferiors[v]
            self.subgraphs[u] = self.__class__(v)
        for u in removed:
            del self.subgraphs[u]
                  
    @trellis.maintain
    def represent(self):
        changes = self.subgraphs.added
        if changes:
            for u in changes:
                if not self.graph.has_node(u):
                    self.graph.add_node(u)
        changes = self.subgraphs.deleted
        if changes:
            for u in changes:
                if self.graph.has_node(u):
                    self.graph.remove_node(u)
        
          
    @trellis.maintain
    def associate(self):
        for u, sub in self.subgraphs.iteritems():
            if not self.graph.has_node(u):
                continue
            peers = set()
            for conn in sub.inferiors.itervalues():
                if isinstance(conn, phub.Hub):
                    continue
                if not conn.connected:
                    continue
                peer = conn.peer.superior
                if peer is None:
                    continue
                if peer.superior is not self.hub:
                    continue
                if peer.name not in self.graph:
                    continue
                peers.add(peer.name)
            neighbors = set(self.graph.neighbors(u))
            added = peers - neighbors
            removed = neighbors - peers
            for v in added:
                self.graph.add_edge(u, v)
            for v in removed:
                self.graph.remove_edge(u, v)

    def snapshot(self):
        graph = self.graph.snapshot()
        
        subgraphs = {}
        for name, sub in self.subgraphs.iteritems():
            subgraphs[name] = sub.snapshot()
        
        return graph, subgraphs

#############################################################################
#############################################################################
