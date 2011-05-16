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
    
    def __nonzero__(self):
        return len(self) > 0
    
    @trellis.compute
    def __len__(self):
        return self.marking.__len__
    
    @trellis.compute
    def __iter__(self):
        return self.marking.__iter__
    
    @trellis.compute
    def __contains__(self):
        return self.marking.__contains__

    def next(self):
        if self.marking:
            yield self.Event(self.pull, items=self.marking)
            
#############################################################################
#############################################################################
