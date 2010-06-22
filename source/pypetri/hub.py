
import warnings
warnings.simplefilter("ignore", DeprecationWarning)

from peak.events import trellis

import pypetri.graph as pgraph

#############################################################################
#############################################################################

class Namable(trellis.Component):

    name = trellis.make(str)
    superior = trellis.attr(None)
    
    @trellis.maintain
    def uid(self):
        return self.compose()
    
    @trellis.maintain
    def superiors(self):
        if self.superior:
            return tuple([self.superior] + list(self.superior.superiors))
        return tuple()
    
    root = property(lambda self: self.superiors[-1] if self.superiors else self)
    
    def compose(self, *args):
        name = self.name
        if self.superior is not None:
            name = self.superior.compose(name, *args)
        return name
    
    def is_super(self, uid):
        return self.uid.startswith(uid)
    
    def is_sub(self, uid):
        return uid.startswith(self.uid)
    
    def __str__(self):
        text = "<%s %s>" \
               % (self.__class__.__name__, 
                  self.uid)
        return text
        
    def __repr__(self):
        text = "<%s name:%r, superior:%r>" \
               % (self.__class__.__name__, 
                  self.name, self.superior)
        return text
    
#############################################################################
#############################################################################

class Connector(Namable):

    peer = trellis.attr(None)
    
    def is_peer(self, uid):
        return self.peer and self.peer.uid == uid

    @trellis.modifier
    def bind(self, other=None):
        self.peer = other
        
#############################################################################
#############################################################################

class Hub(Namable):

    SCOPE_TOKEN = '.'

    def __init__(self, **kwargs):
        super(Hub, self).__init__(**kwargs)
        self.inferiors = trellis.Dict()
    
    def compose(self, *args):
        if self.superior is not None:
            return self.superior.compose(self.name, *args)
        if args:
            name = self.SCOPE_TOKEN.join(map(str, args))
            if self.name:
                name = self.SCOPE_TOKEN.join((str(self.name), name))
            return name
        else:
            return self.name
    
    def decompose(self, name):
        if self.superior is not None:
            names = self.superior.decompose(name)
        else:
            names = name.split(self.SCOPE_TOKEN)
            if self.name:
                index = names.index(self.name)
                names = names[index+1:]
        return names
    
    def find(self, *names):
        if not names:
            return self
        next = names[0]
        names = names[1:]
        inferior = self.inferiors[next]
        if names:
            return inferior.find(*names)
        return inferior

    def get(self, uid):
        names = self.root.decompose(uid)
        return self.root.find(*names)
    
    @trellis.modifier
    def add(self, inferior):
        name = inferior.name
        if name in self.inferiors:
            raise ValueError("Non-unique inferior name: %s" % inferior)
        self.inferiors[name] = inferior
        inferior.superior = self

    @trellis.modifier
    def remove(self, inferior):
        name = inferior.name
        if name in self.inferiors:
            del self.inferiors[name]
            inferior.superior = None
    
    # TODO: inefficient :-(
    @trellis.maintain
    def peerings(self):
        peerings = { }
        for inferior in self.inferiors.itervalues():
            if isinstance(inferior, Hub):
                for p, path in inferior.peerings.iteritems():
                    if path and self.is_sub(path[1]):
                        continue
                    peerings[p] = path
            else:
                peer = inferior.peer
                path = None
                if peer:
                    assert peer.superior is not None
                    path = peer.uid, peer.superior.uid
                peerings[inferior.uid] = path
        return peerings

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
            if isinstance(inferior, Hub) and not inferior.name in self.inferiors:
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
        hubs = [h for h in self.hub.inferiors.itervalues() if isinstance(h, Hub)]
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
                    if isinstance(uobj, Connector):
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
                            if isinstance(vobj, Hub):
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
