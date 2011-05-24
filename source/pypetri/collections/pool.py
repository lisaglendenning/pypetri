# @copyright
# @license

from __future__ import absolute_import

import collections

from .. import trellis
from .. import net

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

    @trellis.modifier
    def send(self, item=None, items=None, add=None):
        if add is None:
            add = self.add
        if item is not None:
            return add(item)
        return self.update(items)

    @trellis.modifier
    def pull(self, items=None):
        marking = self.marking
        if items is None or items is marking:
            return super(Pool, self).pull()
        try:
            itr = iter(items)
        except AttributeError:
            raise TypeError(items)
        pop = self.remove
        for i in itr:
            pop(i)
        return items

#############################################################################
#############################################################################
