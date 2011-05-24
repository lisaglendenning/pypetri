# @copyright
# @license

from __future__ import absolute_import

import collections

from .. import trellis
from .. import net

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
        
    @trellis.modifier
    def send(self, item=None, items=None, add=None):
        if add is None:
            add = self.__setitem__
        if item is not None:
            return add(*item)
        return self.update(items)
        
    @trellis.modifier
    def pull(self, items=None):
        marking = self.marking
        if items is None or items is marking:
            return super(Mapping, self).pull()
        pop = self.pop
        try:
            itr = iter(items)
        except AttributeError:
            raise TypeError(items)
        result = [pop(i) for i in itr]
        return result
    
    @trellis.modifier
    def pop(self, item,):
        if isinstance(item, tuple):
            k = item[0]
        else:
            k = item
        del self[k]
        return item

#############################################################################
#############################################################################
