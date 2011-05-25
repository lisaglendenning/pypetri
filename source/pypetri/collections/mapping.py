# @copyright
# @license

from __future__ import absolute_import

import collections

from .. import trellis

from . import collection

#############################################################################
#############################################################################

class Mapping(collection.Collection, collections.MutableMapping,):

    marking = trellis.make(trellis.Dict)

    @trellis.compute
    def __getitem__(self,):
        return self.marking.__getitem__

    @trellis.compute
    def __delitem__(self,):
        return self.marking.__delitem__

    @trellis.compute
    def __setitem__(self,):
        return self.marking.__setitem__
        
    def copy(self):
        return dict(self.marking)
    
    @trellis.modifier
    def update(self, arg):
        add = self.__setitem__
        if isinstance(arg, tuple) and len(arg) == 2:
            for i in arg:
                if not isinstance(i, tuple):
                    add(*arg)
                    return
        if isinstance(arg, collections.Mapping):
            arg = arg.iteritems()
        for item in arg:
            add(*item)
                
    @trellis.modifier
    def pull(self, arg=None):
        marking = self.marking
        if arg is None or arg is marking:
            return super(Mapping, self).pull()
        pop = self.pop
        if isinstance(arg, tuple) and len(arg) == 2:
            k,v = arg
            try:
                v = pop(k)
            except KeyError:
                pass
            else:
                return k, v
        if isinstance(arg, collections.Hashable):
            k = arg
            if k in marking:
                v = pop(k)
                return k, v
        for k in arg:
            pop(k)
        return arg

#############################################################################
#############################################################################
