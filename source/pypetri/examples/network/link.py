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
from .queue import *

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
