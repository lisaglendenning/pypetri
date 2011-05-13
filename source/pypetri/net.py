# @copyright
# @license

# TODO: could probably improve the code using itertools?

from __future__ import absolute_import

import functools

from . import trellis

from .circuit import *

#############################################################################
# Utility functions
#############################################################################

def brute(itr):
    """Brute force search of all variable-length combinations."""
    def recursor(itr):
        try:
            next = itr.next()
        except StopIteration:
            pass
        else:
            items = [i for i in next]
            for item in items:
                yield [item]
            rest = recursor(itr)
            for combo in rest:
                if len(combo) == 0:
                    continue
                yield combo
                for item in items:
                    yield [item] + combo
    for combo in recursor(itr):
        yield combo

#############################################################################
#############################################################################

class Event(functools.partial):
    pass

#############################################################################
#############################################################################

class Arc(Pipe):
    """Directional link between vertices."""

    @trellis.compute
    def ports(self):
        return (self.input, self.output,)
        
    @trellis.compute
    def connected(self):
        return None not in self.ports

    
#############################################################################
#############################################################################

class Vertex(Switch):
    """Has a set of input Arcs and a set of output Arcs."""
    
    Event = Event

    # TODO: is this buggy?
    @trellis.maintain(make=trellis.Set) # FIXME: DRY
    def inputs(self):
        inputs = self.inputs
        for input in inputs.added:
            if input.output is not self:
                input.output = self
        for input in inputs.removed:
            if input.output is self:
                input.output = None
        return inputs
    
    # TODO: is this buggy?
    @trellis.maintain(make=trellis.Set) # FIXME: DRY
    def outputs(self):
        outputs = self.outputs
        for output in outputs.added:
            if output.input is not self:
                output.input = self
        for output in outputs.removed:
            if output.input is self:
                output.input = None
        return outputs

#############################################################################
#############################################################################

class Condition(Vertex):
    r"""Simple condition that either has some marking or has no marking."""

    marking = trellis.attr(None)

    def send(self, marking=None):
        marking, self.marking = self.marking, marking
        return marking

    def next(self):
        if self.marking:
            yield self.Event(self.send)
    
#############################################################################
#############################################################################

    
class Serializer(Multiplexer):
    """Simple multiplexer that iterates over inputs."""
    
    Event = Event
    
    def next(self, search=None, inputs=None, output=None, *args, **kwargs):
        """Returns an iterator over a set of enabling Events.
        
        There exists some (possibly empty) set of input event
        combinations that satisfy this transition.  This set of possible
        inputs is distinct from the heuristic used to sample this set.
        """
        # A brute-force, general approach is to yield all combinations
        # (n choose k for k in 1..n) of enabling events from all inputs.
        # We don't care about ordering (why we don't do permutations),
        # and there is no repetition.
        search = brute if search is None else search
        inputs = self.inputs if inputs is None else inputs
        output = self.send if output is None else output
    
        def space():
            for i in inputs:
                yield i.next(*args, **kwargs)
            
        for events in search(space()):
            # ignore empty events
            if len(events) == 0:
                continue
            event = self.Event(output, input=None, inputs=events,)
            yield event

    @trellis.modifier
    def send(self, input=None, inputs=None, *args, **kwargs):
        push = self.output.send
        if input is not None:
            push(input, *args, **kwargs)
        if inputs is not None:
            for i in inputs:
                push(i, *args, **kwargs)
        if input is None and inputs is None:
            push(*args, **kwargs)
            
class Tee(Demultiplexer):
    """Copies an input to all outputs."""
    
    Event = Event
    
    @trellis.modifier
    def send(self, input, outputs=None, *args, **kwargs):
        if outputs is None:
            outputs = self.outputs
        for output in outputs:
            output.send(input, *args, **kwargs)


class Exec(Pipe):
    """Pipe operator that executes a function sent to it."""
        
    Event = Event
    
    @trellis.modifier
    def send(self, thunk, *args, **kwargs):
        output = thunk(*args, **kwargs)
        super(Exec, self).send(output)
        
class Transition(Vertex):
    """Simple three-step pipeline of operators."""
    
    @trellis.maintain(make=Serializer)
    def mux(self):
        mux = self.mux
        if mux.inputs is not self.inputs:
            mux.inputs = self.inputs
        if mux.output is not self.pipe:
            mux.output = self.pipe
        return mux
    
    @trellis.maintain(make=Tee)
    def demux(self):
        demux = self.demux
        if demux.input is not self.pipe:
            demux.input = self.pipe
        if demux.outputs is not self.outputs:
            demux.outputs = self.outputs
        return demux
    
    @trellis.maintain(make=Exec)
    def pipe(self):
        pipe = self.pipe
        if pipe.input is not self.mux:
            pipe.input = self.mux
        if pipe.output is not self.demux:
            pipe.output = self.demux
        return pipe
    
    @trellis.compute
    def next(self,):
        try:
            return self.demux.next
        except AttributeError:
            return nada

    @trellis.compute                
    def send(self, thunks, outputs=None):
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

    Arc = Arc
    Condition = Condition
    Transition = Transition

    arcs = trellis.make(trellis.Set)
    vertices = trellis.make(trellis.Set)
    
    def __init__(self, *args, **kwargs):
        for k in 'arcs', 'vertices':
            if k in kwargs:
                kwargs[k] = trellis.Set(kwargs[k])
        super(Network, self).__init__(*args, **kwargs)

    def chain(self, sequence, *args, **kwargs):
        itr = iter(sequence)
        pair = None, itr.next()
        # FIXME: this typechecking may not be the best approach?
        while True:
            pair = pair[1], itr.next()
            if not isinstance(pair[0], self.Arc):
                if not isinstance(pair[1], self.Arc):
                    yield self.link(pair[0], pair[1], *args, **kwargs)
                else:
                    pair[0].outputs.add(pair[1])
            elif not isinstance(pair[1], self.Arc):
                pair[1].inputs.add(pair[0])
            else:
                pair[1].input, pair[0].output = pair
        
    @trellis.modifier
    def link(self, source, sink, Arc=None, *args, **kwargs):
        if Arc is None:
            Arc = self.Arc
        arc = Arc(*args, **kwargs)
        self.arcs.add(arc)
        source.outputs.add(arc)
        sink.inputs.add(arc)
        return arc

    def next(self, vertices=None, *args, **kwargs):
        if vertices is None:
            vertices = self.vertices
        for v in vertices:
            for event in v.next(*args, **kwargs):
                yield event

#############################################################################
#############################################################################
