# @copyright
# @license

import collections

import pypetri.trellis as trellis

#############################################################################
#############################################################################

class Namespace(trellis.Component):

    SUB_TOKEN = '.'
    
    name = trellis.make(str)
    domain = trellis.attr(None)
    
    @trellis.maintain
    def uid(self):
        name = str(self.name)
        if self.domain is not None:
            super = self.domain.uid
            if super:
                name = self.domain.SUB_TOKEN.join((super, name))
        return name
    
    @trellis.maintain
    def enclosures(self):
        if self.domain:
            return tuple([self.domain] + list(self.domain.enclosures))
        return tuple()
    
    top = property(lambda self: self.enclosures[-1] if self.enclosures else self)

    def __str__(self):
        text = "<%s %s>" \
               % (self.__class__.__name__, 
                  self.uid)
        return text
        
    def __repr__(self):
        text = "<%s name:%r, domain:%r>" \
               % (self.__class__.__name__, 
                  self.name, self.domain)
        return text
    
#############################################################################
#############################################################################

class Connector(Namespace):

    peer = trellis.attr(None)
    
    @trellis.modifier
    def connect(self, other):
        if self.connected or other.connected:
            raise RuntimeError((self, other))
        self.peer = other
        other.peer = self
    
    @trellis.modifier
    def disconnect(self):
        if not self.connected:
            raise RuntimeError(self)
        peer = self.peer
        if peer.peer is not self:
            raise RuntimeError((self, peer))
        self.peer = None
        peer.peer = None
        
    @trellis.maintain
    def connected(self):
        return self.peer is not None
        
#############################################################################
#############################################################################

class Composer(Namespace, collections.Mapping):

    def __init__(self, **kwargs):
        super(Composer, self).__init__(**kwargs)
        self.contains = trellis.Dict()
    
    def __getitem__(self, name):
        return self.contains[name]

    def find(self, name):
        names = name.split(self.SUB_TOKEN, 1)
        next = names[0]
        if next not in self:
            raise KeyError(next)
        contained = self.contains[next]
        if len(names) > 1:
            return contained.find(names[1])
        else:
            return contained

    @trellis.modifier
    def add(self, contained):
        name = str(contained.name)
        if name in self:
            raise ValueError("Non-unique component name: %s" % contained)
        self.contains[name] = contained
        contained.domain = self

    @trellis.modifier
    def remove(self, contained):
        name = str(contained.name)
        if name not in self:
            raise ValueError("Not contained: %s" % contained)
        del self.contains[name]
        contained.domain = None
    
    def traverse(self, name):
        contained = self.find(name)
        if not isinstance(contained, Connector):
            raise TypeError(contained)
        return contained.peer
    
#############################################################################
#############################################################################
