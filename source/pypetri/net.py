# @copyright
# @license

r"""Petri Net base."""

from __future__ import absolute_import

import functools
import collections

from . import trellis

from .circuit import *
from .collections import operators

#############################################################################
#############################################################################

class Event(functools.partial):
    pass

#############################################################################
#############################################################################

Arc = Pipe
   
@trellis.modifier
def link(arc, source, sink):
    arc.input = source
    arc.output = sink
    source.outputs.add(arc)
    sink.inputs.add(arc)
    
#############################################################################
#############################################################################

class Vertex(Switch):
    """Has a set of input Arcs and a set of output Arcs."""
    
    Event = Event

    @trellis.maintain(make=trellis.Set)
    def inputs(self):
        # Relying on added/removed seems buggy
        # So do it the slow way
        inputs = self.inputs
        for input in inputs:
            if input.output is not self:
                input.output = self
        return inputs
    
    @trellis.maintain(make=trellis.Set)
    def outputs(self):
        # Relying on added/removed seems buggy
        # So do it the slow way
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

    def send(self, marking=None, *args, **kwargs):
        if marking is not None:
            if isinstance(marking, collections.Iterable):
                for marking in marking:
                    return self.send(marking, *args, **kwargs)
            elif isinstance(marking, collections.Callable):
                marking = marking(*args, **kwargs)
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
    
    @trellis.maintain(make=operators.Combinator)
    def mux(self):
        mux = self.mux
        if mux.inputs is not self.inputs:
            mux.inputs = self.inputs
        if mux.output is not self.pipe:
            mux.output = self.pipe
        return mux
    
    @trellis.maintain(make=operators.Tee)
    def demux(self):
        demux = self.demux
        if demux.input is not self.pipe:
            demux.input = self.pipe
        if demux.outputs is not self.outputs:
            demux.outputs = self.outputs
        return demux
    
    @trellis.maintain(make=operators.Pipeline)
    def pipe(self):
        pipe = self.pipe
        if pipe.input is not self.mux:
            pipe.input = self.mux
        if pipe.output is not self.demux:
            pipe.output = self.demux
        return pipe
    
    def next(self, *args, **kwargs):
        Event = self.Event
        output = self.send
        for event in self.demux.next():
            yield Event(output, event)

    @trellis.compute                
    def send(self,):
        try:
            return self.mux.send
        except AttributeError:
            return nada
    
    # shortcut for executing the first default event
    def __call__(self, *args, **kwargs):
        for event in self.next():
            break
        else: # no events
            raise RuntimeError(self)
        return event(*args, **kwargs)

#############################################################################
#############################################################################

class Network(trellis.Component):

    @trellis.modifier
    def Arc(self, *args, **kwargs):
        arc = Arc(*args, **kwargs)
        self.arcs.add(arc)
        return arc

    @trellis.modifier
    def Condition(self, *args, **kwargs):
        condition = Condition(*args, **kwargs)
        self.conditions.add(condition)
        return condition
    
    @trellis.modifier
    def Transition(self, *args, **kwargs):
        transition = Transition(*args, **kwargs)
        self.transitions.add(transition)
        return transition
    
    arcs = trellis.make(trellis.Set)
    transitions = trellis.make(trellis.Set)
    conditions = trellis.make(trellis.Set)
    
    def __init__(self, *args, **kwargs):
        for k in 'arcs', 'vertices':
            if k in kwargs:
                kwargs[k] = trellis.Set(kwargs[k])
        super(Network, self).__init__(*args, **kwargs)

    def next(self, transitions=None, *args, **kwargs):
        if transitions is None:
            transitions = self.transitions
        for t in transitions:
            for event in t.next(*args, **kwargs):
                yield event
    
    @trellis.modifier
    def __call__(self, *args, **kwargs):
        for event in self.next():
            break
        else:
            raise RuntimeError(self)
        return event(*args, **kwargs)

#############################################################################
#############################################################################
