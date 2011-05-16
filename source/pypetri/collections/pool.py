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
    def send(self, *args):
        marking = self.marking
        marking.update(args)

    @trellis.modifier
    def pull(self, item=None, items=None, pop=None):
        if pop is None:
            pop = self.remove
        if item is not None:
            pop(item)
            return item
        marking = self.marking
        if items is marking:
            items = marking.copy()
            marking.clear()
        else:
            try:
                itr = iter(items)
            except AttributeError:
                raise TypeError(items)
            for item in itr:
                pop(item)
        return items

#############################################################################
#############################################################################
