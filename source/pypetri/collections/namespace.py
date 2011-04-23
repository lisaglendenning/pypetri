# @copyright
# @license

from __future__ import absolute_import

import collections

from . import trellis

#############################################################################
#############################################################################

class Namable(collections.Hashable, trellis.Component):

    SUB_TOKEN = '.'
    TEMPLATE = '<%s>'
    
    name = trellis.make(str)
    domain = trellis.attr(None)

    def isa(self, cls):
        return isinstance(self, cls)

    def __cmp__(self, other):
        if other is not None:
            other = str(other)
        return cmp(str(self), other)
    
    def __eq__(self, other):
        if self.isa(other.__class__):
            return self.uid == other.uid
        return False
    
    @trellis.maintain
    def __str__(self):
        value = str(self.name)
        return lambda: value
    
    @trellis.maintain
    def __hash__(self):
        value = hash(self.name)
        return lambda: value
    
    def join(self, *names):
        return self.SUB_TOKEN.join([str(n) for n in names if n])

    def split(self, name):
        return name.split(self.SUB_TOKEN, 1)
    
    @trellis.maintain
    def uid(self):
        domain = self.domain
        if domain is None:
            return self.join(self.name)
        else:
            return domain.join(domain.uid, self.name)
    
    @trellis.maintain
    def enclosures(self):
        if self.domain:
            return tuple([self.domain] + list(self.domain.enclosures))
        return tuple()
    
    @trellis.maintain
    def top(self):
        if self.domain is None:
            return self
        return self.domain.top

    def __repr__(self):
        text = self.__class__.__name__
        keys = 'uid',
        if keys:
            attrs = [':'.join((k, str(getattr(self, k)))) for k in keys]
            text += ' ' + ', '.join(attrs)
        return self.TEMPLATE % text

#############################################################################
#############################################################################

class Namespace(Namable, collections.MutableMapping):
    
    named = trellis.make(trellis.Dict)

    def __init__(self, named=(), **kwargs):
        Namable.__init__(self, named=trellis.Dict(named), **kwargs)

    def __eq__(self, other):
        return Namable.__eq__(self, other) and collections.Mapping.__eq__(self, other)
    
    def __contains__(self, name):
        if not isinstance(name, str):
            name = str(name)
        return name in self.named
    
    def __getitem__(self, name):
        if not isinstance(name, str):
            name = str(name)
        return self.named[name]
    
    @trellis.modifier
    def __setitem__(self, name, namable):
        if not isinstance(name, str):
            name = str(name)
        if name in self:
            del self[name]
        self.named[name] = namable
        namable.domain = self
    
    @trellis.modifier
    def __delitem__(self, name):
        if not isinstance(name, str):
            name = str(name)
        if name not in self:
            raise KeyError
        else:
            namable = self[name]
            namable.domain = None
            del self[name]
        
    def __len__(self):
        return len(self.named)
    
    def __iter__(self):
        return iter(self.named)

    def find(self, name):
        names = self.split(name)
        next = names[0]
        if next not in self:
            return None
        next = self[next]
        if len(names) > 1:
            return next.find(names[1])
        else:
            return next

    def add(self, namable):
        self[namable.name] = namable

    def remove(self, namable):
        del self[namable.name]

#############################################################################
#############################################################################
