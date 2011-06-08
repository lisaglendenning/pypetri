# @copyright
# @license

from __future__ import absolute_import

from .. import trellis
from .. import net

#############################################################################
#############################################################################

class Collection(net.Condition,):
    
    def __hash__(self):
        return object.__hash__(self)
    
    def __eq__(self, other):
        return self is other
    
    @trellis.compute
    def __nonzero__(self):
        return self.marking.__nonzero__
    
    @trellis.compute
    def __len__(self):
        return self.marking.__len__
    
    @trellis.compute
    def __iter__(self):
        return self.marking.__iter__
    
    @trellis.compute
    def __contains__(self):
        return self.marking.__contains__
    
    @trellis.compute
    def clear(self):
        return self.marking.clear
    
    @trellis.compute
    def send(self):
        return self.update
    
    @trellis.modifier
    def pull(self):
        marking = self.copy()
        self.clear()
        return marking

    def next(self, select=None):
        if not len(self):
            return
        if select is None:
            yield self.Event(self.pull,)
        else:
            for selection in select(self):
                yield self.Event(self.pull, selection)
            
#############################################################################
#############################################################################
