# @copyright
# @license

r"""Petri Net base."""

from __future__ import absolute_import

import functools
import inspect

from . import trellis

from . import circuit
from . import operators
from .collections import sets

#############################################################################
#############################################################################

class Event(functools.partial):
    
    def __new__(cls, *args, **kwargs):
        obj = super(Event, cls).__new__(cls, *args, **kwargs)
        if inspect.ismethod(obj.func):
            obj.self = obj.func.im_self
        return obj

#############################################################################
#############################################################################

Arc = operators.Pipe
   
@trellis.modifier
def link(arc, source, sink):
    arc.input = source
    arc.output = sink
    source.outputs.add(arc)
    sink.inputs.add(arc)
    
#############################################################################
#############################################################################

class Vertex(trellis.Component, circuit.Switch):
    """Has a set of input Arcs and a set of output Arcs."""
    
    Event = Event

    @trellis.maintain(make=sets.Set)
    def inputs(self):
        # O(n)
        inputs = self.inputs
        for input in inputs:
            if input.output is not self:
                input.output = self
        return inputs
    
    @trellis.maintain(make=sets.Set)
    def outputs(self):
        # O(n)
        outputs = self.outputs
        for output in outputs:
            if output.input is not self:
                output.input = self
        return outputs

#############################################################################
#############################################################################

class Condition(Vertex):
    r"""Simple condition that either has some marking or has no marking."""

    marking = trellis.attr(None)

    @trellis.modifier
    def send(self, marking=None):
        marking, self.marking = self.marking, marking
        return marking

    def next(self):
        if self.marking:
            yield self.Event(self.send)

#############################################################################
#############################################################################

class Transition(Vertex):
    """Simple three-step pipeline of operators."""
    
    Event = Event
    
    Multiplexer = operators.Combinator
    Demultiplexer = operators.Tee
    Pipe = operators.Pipe
    
    @trellis.maintain(make=lambda self: self.Multiplexer())
    def mux(self):
        mux = self.mux
        if mux.inputs is not self.inputs:
            mux.inputs = self.inputs
        if mux.output is not self.pipe:
            mux.output = self.pipe
        return mux
    
    @trellis.maintain(make=lambda self: self.Demultiplexer())
    def demux(self):
        demux = self.demux
        if demux.input is not self.pipe:
            demux.input = self.pipe
        if demux.outputs is not self.outputs:
            demux.outputs = self.outputs
        return demux
    
    @trellis.maintain(make=lambda self: self.Pipe())
    def pipe(self):
        pipe = self.pipe
        if pipe.input is not self.mux:
            pipe.input = self.mux
        if pipe.output is not self.demux:
            pipe.output = self.demux
        return pipe
    
    @trellis.compute
    def next(self):
        fn = self.pass_in(self.demux)
        Event = self.Event
        send = self.send
        def next(*args, **kwargs):
            for input in fn(*args, **kwargs):
                yield Event(send, input)
        return next

    @trellis.compute                
    def send(self):
        return self.pass_out(self.mux)
    
    # shortcut for executing the first default event
    def __call__(self, *args, **kwargs):
        for event in self.next(*args, **kwargs):
            break
        else: # no events
            raise StopIteration
        return event()

#############################################################################
#############################################################################

class Network(trellis.Component):

    @trellis.modifier
    def Arc(self, source, sink, arc=None):
        if arc is None:
            arc = Arc(input=source, output=sink)
        self.arcs.add(arc)
        link(arc, source, sink)
        return arc

    @trellis.modifier
    def Condition(self, Condition=Condition, *args, **kwargs):
        condition = Condition(*args, **kwargs)
        self.conditions.add(condition)
        return condition
    
    @trellis.modifier
    def Transition(self, Transition=Transition, *args, **kwargs):
        transition = Transition(*args, **kwargs)
        self.transitions.add(transition)
        return transition
    
    @trellis.modifier
    def linked(self, source, sink, **kwargs):
        Arc = self.Arc
        for o in source.outputs:
            if o.output is sink:
                return o
        return Arc(source, sink, **kwargs)
            
    arcs = trellis.make(sets.Set)
    transitions = trellis.make(sets.Set)
    conditions = trellis.make(sets.Set)

    @trellis.compute
    def next(self,):
        ts = self.transitions
        def next(transitions=iter, *args, **kwargs):
            transitions = transitions(ts)
            for t in transitions:
                for event in t.next(*args, **kwargs):
                    yield event
        return next
    
    @trellis.modifier
    def __call__(self, *args, **kwargs):
        for event in self.next(*args, **kwargs):
            break
        else:
            raise StopIteration
        return event()

#############################################################################
#############################################################################
