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
    def links(self):
        updates = (self.inputs, 'output'), (self.outputs, 'input'),
        for collection, attr in updates:
            for arc in collection.added:
                if getattr(arc, attr) is not self:
                    setattr(arc, attr, self)
            for arc in collection.removed:
                if getattr(arc, attr) is self:
                    setattr(arc, attr, None)

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
            # ignore empty events
            if len(events) == 0:
                continue
            event = self.Event(output, events,)
            yield event
    
    @trellis.modifier                
    def send(self, thunks, outputs=None):
        if outputs is None:
            outputs = self.outputs
        for thunk in thunks:
            input = thunk()
            for output in outputs:
                output.send(input)

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
