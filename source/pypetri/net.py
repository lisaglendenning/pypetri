# @copyright
# @license

r"""Petri Net base."""

from __future__ import absolute_import

import functools
import collections

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
    
    @trellis.modifier
    def link(self, source, sink):
        source.outputs.add(self)
        sink.inputs.add(self)

    
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
    
class Combinator(Multiplexer):
    """Iterates over all possible inputs."""
    
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
            event = self.Event(output, events,)
            yield event
            
#############################################################################
#############################################################################

class Tee(Demultiplexer):
    """Copies an input to all outputs."""
    
    @trellis.modifier
    def send(self, input, outputs=None, *args, **kwargs):
        if outputs is None:
            outputs = self.outputs
        for output in outputs:
            output.send(input, *args, **kwargs)
        
#############################################################################
#############################################################################

class Pipeline(Pipe, collections.Iterable,):
    """Chain of pipe operators."""
    
    pipes = trellis.make(list) # TODO: linked list would be better
    
    @trellis.maintain
    def _links(self):
        pipes = self.pipes
        npipes = len(pipes)
        for i in xrange(npipes):
            if i > 0:
                input = pipes[i-1]
            else:
                input = self.input
            if pipes[i].input is not input:
                pipes[i].input = input
            if i < npipes-1:
                output = pipes[i+1]
            else:
                output = self.output
            if pipes[i].output is not output:
                pipes[i].output = output
        return pipes
    
    def __nonzero__(self):
        return len(self) > 0
    
    @trellis.compute
    def __len__(self):
        return self.pipes.__len__
    
    @trellis.compute
    def __iter__(self):
        return self.pipes.__iter__
    
    @trellis.compute
    def __getitem__(self):
        return self.pipes.__getitem__
        
    @trellis.modifier
    def append(self, item):
        pipes = self.pipes
        pipes.append(item)
        trellis.on_undo(self.pipes.pop)
        if len(pipes) > 1:
            input = pipes[-2]
            prev = input.output
            input.output = item
            trellis.on_undo(setattr, input, 'output', prev,)
        else:
            input = self.input
        prev = item.input
        item.input = input
        trellis.on_undo(setattr, item, 'input', prev,)
        prev = item.output
        item.output = self.output
        trellis.on_undo(setattr, item, 'output', prev,)
    
    @trellis.compute
    def __delitem__(self):
        return self.pipes.__delitem__
        
    @trellis.compute
    def insert(self):
        return self.pipes.insert
    
    @trellis.compute
    def send(self):
        output = self[0] if len(self) else self.output
        if output is not None:
            return output.send
        else:
            return nada
        
    @trellis.compute
    def next(self):
        input = self[-1] if len(self) else self.input
        if input is not None:
            return input.next
        else:
            return nada

#############################################################################
#############################################################################

class Exec(Pipe):
    """Pipe operator that executes a function sent to it."""
    
    @trellis.modifier
    def send(self, thunk, *args, **kwargs):
        output = thunk(*args, **kwargs)
        super(Exec, self).send(output)
        
class Iter(Pipe):
    """Pipe operator that iterates over input."""

    @trellis.modifier
    def send(self, inputs, *args, **kwargs):
        for input in inputs:
            super(Iter, self).send(input, *args, **kwargs)

class Apply(Pipe):
    """Pipe operator that applies a function to its input."""
    
    fn = trellis.attr(None)
    
    @trellis.modifier
    def send(self, input, *args, **kwargs):
        output = self.fn(input, *args, **kwargs)
        super(Apply, self).send(output)
        
#############################################################################
#############################################################################

class Transition(Vertex):
    """Simple three-step pipeline of operators."""
    
    @trellis.maintain(make=Combinator)
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
    
    @trellis.maintain(make=Pipeline)
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
