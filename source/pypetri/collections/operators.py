# @copyright
# @license


from __future__ import absolute_import

import collections

from . import trellis
from ..circuit import *

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

class Call(Pipe):
    """Pipe operator that calls an input zero-argument function."""
    
    @trellis.modifier
    def send(self, thunk, *args, **kwargs):
        output = thunk()
        super(Call, self).send(output, *args, **kwargs)
        
class Iter(Pipe):
    """Pipe operator that iterates over input."""

    @trellis.modifier
    def send(self, inputs, *args, **kwargs):
        for input in inputs:
            super(Iter, self).send(input, *args, **kwargs)

class Apply(Pipe):
    """Pipe operator that applies a function to input."""
    
    fn = trellis.attr(None)
    
    @trellis.modifier
    def send(self, input, *args, **kwargs):
        output = self.fn(input)
        super(Apply, self).send(output, *args, **kwargs)
        
class FilterIn(Pipe):
    """Pipe operator that applies a filter to input."""
    
    fn = trellis.attr(None)
    
    def next(self, *args, **kwargs):
        filter = self.fn
        for event in super(FilterIn, self).next(*args, **kwargs):
            for filtered in filter(event):
                yield filtered
        
class FilterOut(Pipe):
    """Pipe operator that applies a filter to output."""
    
    fn = trellis.attr(None)
    
    @trellis.modifier
    def send(self, input, *args, **kwargs):
        filter = self.fn
        for output in filter(input):
            super(FilterOut, self).send(output, *args, **kwargs)

#############################################################################
#############################################################################
    
class Combinator(Multiplexer):
    """Iterates over all combinations of inputs."""

    def next(self, search=None, inputs=None, *args, **kwargs):
        # A brute-force, general approach is to yield all combinations
        # (n choose k for k in 1..n) of enabling events from all inputs.
        # We don't care about ordering (why we don't do permutations),
        # and there is no repetition.
        search = brute if search is None else search
        inputs = self.inputs if inputs is None else inputs
    
        def space():
            for i in inputs:
                yield i.next(*args, **kwargs)
            
        for events in search(space()):
            # ignore empty events
            if len(events) == 0:
                continue
            yield events
            
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
    
    head = trellis.attr(None)
    tail = trellis.attr(None)
    
    def __init__(self, *args, **kwargs):
        super(Pipeline, self).__init__(**kwargs)
        for arg in args:
            self.append(arg)

    @trellis.maintain
    def _pipes(self):
        head = self.head
        if head is None:
            return
        if head.input is not self.input:
            head.input = self.input
        tail = self.tail
        if tail.output is not self.output:
            tail.output = self.output
    
    def __iter__(self):
        next = self.head
        while next is not None:
            yield next
            next = next.output
            if next is self.tail:
                break
        
    @trellis.modifier
    def append(self, item):
        tail = self.tail
        if tail is None:
            self.head = item
        else:
            tail.output = item
            item.input = tail
        self.tail = item
    
    @trellis.modifier
    def pop(self,):
        tail = self.tail
        if tail is None:
            raise ValueError(self)
        else:
            if tail is self.head:
                self.head = None
                self.tail = None
            else:
                self.tail = tail.input
        tail.input = None
        tail.output = None
        return tail
            
    @trellis.compute
    def send(self):
        output = self.head if self.head is not None else self.output
        if output is not None:
            return output.send
        else:
            return nada
        
    @trellis.compute
    def next(self):
        input = self.tail if self.tail is not None else self.input
        if input is not None:
            return input.next
        else:
            return nada

#############################################################################
#############################################################################
