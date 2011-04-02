
import pypetri.trellis

#############################################################################
#############################################################################

class Namable(pypetri.trellis.Component):

    SUB_TOKEN = '.'
    
    name = pypetri.trellis.make(str)
    superior = pypetri.trellis.attr(None)
    
    @pypetri.trellis.maintain
    def uid(self):
        return self.compose()
    
    @pypetri.trellis.maintain
    def superiors(self):
        if self.superior:
            return tuple([self.superior] + list(self.superior.superiors))
        return tuple()
    
    root = property(lambda self: self.superiors[-1] if self.superiors else self)
    
    def compose(self):
        name = str(self.name)
        if self.superior is not None:
            super = self.superior.compose()
            if super:
                name = self.superior.SUB_TOKEN.join((super, name))
        return name
    
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

    peer = pypetri.trellis.attr(None)
    
    @pypetri.trellis.modifier
    def connect(self, other):
        if self.connected or other.connected:
            raise RuntimeError((self, other))
        self.peer = other
        other.peer = self
    
    @pypetri.trellis.modifier
    def disconnect(self):
        if not self.connected:
            raise RuntimeError(self)
        peer = self.peer
        if peer.peer is not self:
            raise RuntimeError((self, peer))
        self.peer = None
        peer.peer = None
        
    @pypetri.trellis.maintain
    def connected(self):
        return self.peer is not None
        
#############################################################################
#############################################################################

class Hub(Namable):

    def __init__(self, **kwargs):
        super(Hub, self).__init__(**kwargs)
        self.inferiors = pypetri.trellis.Dict()
    
    def is_superior(self, uid):
        return uid.startswith(self.uid)
    
    def is_inferior(self, uid):
        return self.uid.startswith(uid)
    
#    def decompose(self, prefix, *names):
#        names = name.rsplit(self.SCOPE_TOKEN, 1)
#        if self.superior is not None:
#            names = self.superior.decompose(name)
#        else:
#            names = name.split(self.SCOPE_TOKEN, 1)
#            if self.name:
#                index = names.index(self.name)
#                names = names[index+1:]
#        return names
    
    def find(self, name):
        names = name.split(self.SUB_TOKEN, 1)
        next = names[0]
        if next not in self.inferiors:
            raise KeyError(next)
        inferior = self.inferiors[next]
        if len(names) > 1:
            return inferior.find(names[1])
        else:
            return inferior

#    def get(self, uid):
#        if uid == self.name:
#            return self
#        names = self.root.decompose(uid)
#        return self.root.find(*names)
    
    @pypetri.trellis.modifier
    def add(self, inferior):
        name = str(inferior.name)
        if name in self.inferiors:
            raise ValueError("Non-unique inferior name: %s" % inferior)
        self.inferiors[name] = inferior
        inferior.superior = self

    @pypetri.trellis.modifier
    def remove(self, inferior):
        name = str(inferior.name)
        if name not in self.inferiors:
            raise ValueError("Not an inferior: %s" % inferior)
        del self.inferiors[name]
        inferior.superior = None
    
    def traverse(self, name):
        inferior = self.find(name)
        if not isinstance(inferior, Connector):
            raise ValueError(inferior)
        return inferior.peer
    
    # TODO: inefficient :-(
    # TODO: is this function necessary?
#    @pypetri.trellis.maintain
#    def peerings(self):
#        peerings = { }
#        for inferior in self.inferiors.itervalues():
#            if isinstance(inferior, Hub):
#                for p, path in inferior.peerings.iteritems():
#                    if path and self.is_superior(path[1]):
#                        continue
#                    peerings[p] = path
#            else:
#                peer = inferior.peer
#                path = None
#                if peer:
#                    assert peer.superior is not None
#                    path = peer.uid, peer.superior.uid
#                peerings[inferior.uid] = path
#        return peerings

#############################################################################
#############################################################################
