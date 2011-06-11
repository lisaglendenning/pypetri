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
    
    def Condition(self, **kwargs):
        return super(Link, self).Condition(Condition=Queue, **kwargs)
    
    def Transition(self, **kwargs):
        pipe = operators.Pipeline(operators.Iter(), operators.Call())
        return super(Link, self).Transition(pipe=pipe, **kwargs)
    
    @trellis.maintain(make=lambda self: self.Condition())
    def input(self):
        r"""Input queue."""
        return self.input
    
    @trellis.maintain(make=lambda self: self.Condition())
    def output(self):
        r"""Output queue."""
        return self.output
    
    @trellis.maintain(make=lambda self: self.Transition())
    def deliver(self):
        r"""Dequeue an input message and enqueue in output."""
        transition = self.deliver
        inputs = self.input,
        for input in inputs:
            self.linked(input, transition)
        outputs = self.output,
        for output in outputs:
            self.linked(transition, output)
        return transition
        
    @trellis.maintain(make=lambda self: self.Transition())
    def drop(self):
        r"""Dequeue an input message."""
        transition = self.drop
        inputs = self.input,
        for input in inputs:
            self.linked(input, transition)
        return transition
    
    @trellis.maintain(make=lambda self: self.Transition())
    def duplicate(self):
        r"""Dequeue an input message and enqueue in input and output."""
        transition = self.duplicate
        inputs = self.input,
        for input in inputs:
            self.linked(input, transition)
        outputs = self.output, self.input
        for output in outputs:
            self.linked(transition, output)
        return transition
    
    @trellis.maintain(make=lambda self: self.Transition())
    def delay(self):
        r"""Dequeue and enqueue an input message."""
        transition = self.delay
        inputs = self.input,
        for input in inputs:
            self.linked(input, transition)
        outputs = inputs
        for output in outputs:
            self.linked(transition, output)
        return transition
    
#############################################################################
#############################################################################
