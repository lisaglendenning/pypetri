
import warnings
warnings.simplefilter("ignore", DeprecationWarning)

from peak.events import trellis

import pypetri.hub as phub
import pypetri.graph.graph as pgraph

#############################################################################
#############################################################################

class HubGraph(trellis.Component):

    hub = trellis.make(None)
    links = trellis.make(None)
    inferiors = trellis.make(None)
    
    def __init__(self, hub, **kwargs):
        if 'links' not in kwargs:
            kwargs['links'] = pgraph.Graph()
        if 'inferiors' not in kwargs:
            kwargs['inferiors'] = {}
        super(HubGraph, self).__init__(hub=hub, **kwargs)
        self.links.add_node(self.hub.uid)
    
    @trellis.maintain
    def associate(self):
        root = self.hub.root
        for inferior in self.hub.inferiors.itervalues():
            if not self.links.has_node(inferior.uid):
                self.links.add_node(inferior.uid)
            edge = (self.hub.uid, inferior.uid)
            if not self.links.has_edge(*edge):
                self.links.add_edge(*edge)
            if isinstance(inferior, phub.Hub) and not inferior.name in self.inferiors:
                self.inferiors[inferior.name] = HubGraph(inferior)
        nbunch = []
        for u in self.links.nodes_iter():
            try:
                root.get(u)
            except KeyError:
                nbunch.append(u)
        self.links.remove_nodes_from(nbunch)
        for name in self.inferiors:
            if name not in self.hub.inferiors:
                del self.inferiors[name]

    @trellis.maintain
    def reassociate(self):
        hubs = [h for h in self.hub.inferiors.itervalues() if isinstance(h, phub.Hub)]
        for hub in hubs:
            for c, path in hub.peerings.iteritems():
                if not self.links.has_node(c):
                    self.links.add_node(c)
                if path:
                    p = path[0]
                    if not self.links.has_node(p):
                        self.links.add_node(p)
                    self.peered(c, p)
        nbunch = []
        ebunch = []
        root = self.hub.root
        for u in self.links.nodes_iter():
            try:
                uobj = root.get(u)
            except KeyError:
                nbunch.append(u)
            else:
                for v in self.links.neighbors_iter(u):
                    if uobj.is_super(v):
                        continue
                    if isinstance(uobj, phub.Connector):
                        if uobj.is_peer(v):
                            continue
                    else:
                        if v in uobj.peerings:
                            continue
                        try:
                            vobj = root.get(v)
                        except KeyError:
                            continue
                        else:
                            if isinstance(vobj, phub.Hub):
                                continue
                    ebunch.append((u,v))
        self.links.remove_edges_from(ebunch)
        self.links.remove_nodes_from(nbunch)
    
    def peered(self, c1, c2):
        edge = (c1, c2)
        if not self.links.has_edge(*edge):
            self.links.add_edge(*edge)    
    
    def snapshot(self):
        subgraphs = {}
        for name, inferior in self.inferiors.iteritems():
            subgraphs[name] = inferior.snapshot()
        
        graph = self.links.snapshot()
        for name, subgraph in subgraphs.iteritems():
            graph.add_nodes_from(subgraph.nodes_iter()) 
            graph.add_edges_from(subgraph.edges_iter())
        return graph

#############################################################################
#############################################################################
