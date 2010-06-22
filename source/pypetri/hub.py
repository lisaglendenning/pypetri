
import warnings
warnings.simplefilter("ignore", DeprecationWarning)

from peak.events import trellis

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
        if uid == self.name:
            return self
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
