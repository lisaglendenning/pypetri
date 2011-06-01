# @copyright
# @license

from __future__ import absolute_import

import collections

from .. import trellis

from . import collection

#############################################################################
#############################################################################

class Pool(collection.Collection, collections.MutableSet,):
    
    marking = trellis.make(trellis.Set)
    
    @trellis.compute
    def add(self):
        return self.marking.add

    @trellis.compute
    def discard(self):
        return self.marking.discard
    
    def copy(self):
        return set(self.marking)

    @trellis.modifier
    def update(self, *args):
        add = self.add
        # won't work for all contained types
        if len(args) == 1:
            if not isinstance(args[0], collections.Hashable):
                args = args[0]
        for arg in args:
            add(arg)

    @trellis.modifier
    def pull(self, arg=None):
        marking = self.marking
        if arg is None or arg is marking:
            return super(Pool, self).pull()
        pop = self.remove
        if isinstance(arg, collections.Hashable) and arg in marking:
            pop(arg)
            return arg
        for i in arg:
            pop(i)
        return arg

#############################################################################
#############################################################################
