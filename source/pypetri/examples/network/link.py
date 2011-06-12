# @copyright
# @license

r"""Simple model of an asynchronous network link.

A network link has an input queue and an output queue.
A network link delivers the message at the head of the input queue
to the tail of the output queue.
Messages in the input queue can be delayed, duplicated, or dropped.
"""

from __future__ import absolute_import

from pypetri import net, trellis, operators
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

class Link(net.Network):
    
    @trellis.modifier
    def Arcs(self):
        input = self.input
        for transition in self.deliver, self.delay, self.drop, self.duplicate:
            self.Arc(input, transition)
        output = self.output
        for transition in self.deliver, self.duplicate:
            self.Arc(transition, output)
        for transition in self.delay, self.duplicate:
            self.Arc(transition, input)
    
    def Condition(self, **kwargs):
        return super(Link, self).Condition(Condition=Queue, **kwargs)
    
    def Transition(self, **kwargs):
        pipe = operators.Pipeline(operators.Iter(), operators.Call())
        return super(Link, self).Transition(pipe=pipe, **kwargs)
    
    def __init__(self, *args, **kwargs):
        super(Link, self).__init__(*args, **kwargs)
        self.Arcs()
        
    # Input queue
    input = trellis.make(lambda self: self.Condition())
    # Output queue
    output = trellis.make(lambda self: self.Condition())
    
    # Dequeue an input message and enqueue in output
    deliver = trellis.make(lambda self: self.Transition())
    # Dequeue an input message and enqueue in input and output
    duplicate = trellis.make(lambda self: self.Transition())
    # Dequeue and enqueue an input message
    delay = trellis.make(lambda self: self.Transition())
    # Dequeue an input message
    drop = trellis.make(lambda self: self.Transition())

#############################################################################
#############################################################################

class Channel(net.Network):
    r"""Bidirectional link."""
        
    sending = trellis.make(Link)
    receiving = trellis.make(Link)

#############################################################################
#############################################################################
