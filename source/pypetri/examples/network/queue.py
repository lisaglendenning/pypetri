# @copyright
# @license

from __future__ import absolute_import

from pypetri import trellis
from pypetri.collections import collection, queue

#############################################################################
#############################################################################

class Queue(collection.Collection):

    marking = trellis.make(queue.Queue)
    
    @trellis.compute
    def __getitem__(self):
        return self.marking.__getitem__
    
    @trellis.compute
    def enqueue(self):
        return self.marking.enqueue
    
    @trellis.compute
    def dequeue(self):
        return self.marking.dequeue
    
    @trellis.compute
    def head(self):
        return self.marking.head
    
    @trellis.compute
    def tail(self):
        return self.marking.tail
    
    @trellis.modifier
    def pull(self, item):
        self.dequeue()
        return item
    
    @trellis.modifier
    def send(self, *args):
        for arg in args:
            self.enqueue(arg)
    
    def next(self):
        if len(self):
            yield self.Event(self.pull, self.head)

#############################################################################
#############################################################################
