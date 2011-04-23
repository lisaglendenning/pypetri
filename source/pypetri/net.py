# @copyright
# @license

# TODO: could probably improve the code using itertools?

from __future__ import absolute_import

import functools

from . import trellis

#############################################################################
#############################################################################

def brute(itr):
    """Brute force search of all variable-length combinations."""
    def recursor(itr):
        try:
            next = itr.next()
        except StopIteration:
            pass
        else:
            rest = recursor(itr)
            for combo in rest:
                for item in next:
                    yield [item] + combo
        finally:
            yield []
    for combo in recursor(itr):
        yield combo

#############################################################################
#############################################################################

Event = functools.partial

#############################################################################
#############################################################################

class Arc(trellis.Component):
    """Directional link."""

    input = trellis.attr(None)
    output = trellis.attr(None)
    
    @trellis.maintain
    def ports(self):
        return (self.input, self.output,)
        
    @trellis.maintain
    def connected(self):
        return None not in self.ports

    @trellis.maintain
    def send(self):
        output = self.output
        if output is None:
            return None
        return output.send

    @trellis.maintain
    def next(self):
        input = self.input
        if input is None:
            return None
        return input.next
    
#############################################################################
#############################################################################

class Vertex(trellis.Component):
    """Has a set of input Arcs and a set of output Arcs."""
    
    Event = Event
    
    inputs = trellis.make(trellis.Set)
    outputs = trellis.make(trellis.Set)
    
    @trellis.maintain
    def link(self): # FIXME: optimize
        for input in self.inputs:
            if input.output is not self:
                input.output = self
        for output in self.outputs:
            if output.input is not self:
                output.input = self

#############################################################################
#############################################################################

class Condition(Vertex):

    marking = trellis.attr(None)

    def send(self, marking=None):
        marking, self.marking = self.marking, marking
        return marking

    def next(self):
        if self.marking:
            yield self.Event(self.send)
    
#############################################################################
#############################################################################

class Transition(Vertex):
                    
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
            event = self.Event(output, events,)
            yield event
    
    @trellis.modifier                
    def send(self, inputs, outputs=None):
        if outputs is None:
            outputs = self.outputs
        for input in inputs:
            input = input()
            for output in outputs:
                output.send(input)

#############################################################################
#############################################################################

class Network(trellis.Component):

    Arc = Arc
    Condition = Condition
    Transition = Transition

    def link(self, sequence=None, Arc=None, *args, **kwargs):
        if sequence is None:
            sequence = self.vertices
        if Arc is None:
            Arc = self.Arc
        itr = iter(sequence)
        pair = None, itr.next()
        while True:
            pair = [self[x] if isinstance(x, str) else x for x in pair[1], itr.next()]
            if pair[0] in self.vertices:
                if pair[1] in self.vertices:
                    # need to create a new arc
                    arc = Arc(*args, **kwargs)
                    self.arcs.add(arc)
                    pair[0].outputs.add(arc)
                    pair[1].inputs.add(arc)
                    yield arc
                else:
                    pair[0].outputs.add(pair[1])
            elif pair[1] in self.vertices:
                pair[1].inputs.add(pair[0])
            else:
                pair[1].input, pair[0].output = pair
    
    arcs = trellis.make(trellis.Set)
    vertices = trellis.make(trellis.Set)
    
    def __init__(self, *args, **kwargs):
        for k in 'arcs', 'vertices':
            if k in kwargs:
                kwargs[k] = trellis.Set(kwargs[k])
        super(Network, self).__init__(*args, **kwargs)

    def next(self, vertices=None, *args, **kwargs):
        if vertices is None:
            vertices = self.vertices
        for v in vertices:
            for event in v.next(*args, **kwargs):
                yield event

#############################################################################
#############################################################################
