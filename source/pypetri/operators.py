# @copyright
# @license


from __future__ import absolute_import

import collections
import itertools

from . import trellis

from . import circuit

#############################################################################
#############################################################################

def flatten(arg, filter=None, types=(list, tuple,)):
    if filter is None:
        filter = lambda x: not isinstance(x, types)
    if filter(arg):
        yield arg
        return
    iterable = iter(arg)
    while True:
        try:
            i = iterable.next()
        except StopIteration:
            return
        if filter(i):
            yield i
        elif isinstance(i, types):
            try:
                i = iter(i)
            except TypeError:
                pass
            else:
                iterable = itertools.chain(i, iterable)
                
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

class Pipe(trellis.Component, circuit.Pipe):
    
    input = trellis.attr(None)
    output = trellis.attr(None)
    
    @trellis.compute
    def send(self):
        return self.pass_out(self.output)

    @trellis.compute
    def next(self):
        return self.pass_in(self.input)
    
    
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
    def send(self, *args, **kwargs):
        output = self.fn(*args, **kwargs)
        super(Apply, self).send(output)
        
class Flatten(Pipe):
    """Pipe operator that flattens input."""

    @trellis.modifier
    def send(self, input):
        if isinstance(input, collections.Mapping):
            super(Flatten, self).send(**input)
        else:
            super(Flatten, self).send(*input)
        
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
        return self.pass_out(output)
        
    @trellis.compute
    def next(self):
        input = self.tail if self.tail is not None else self.input
        return self.pass_in(input)

#############################################################################
#############################################################################

class Multiplexer(trellis.Component, circuit.Multiplexer):

    inputs = trellis.attr(None)
    output = trellis.attr(None)
    
    @trellis.compute
    def send(self):
        return self.pass_out(self.output)


class Combinator(Multiplexer):
    """Iterates over all combinations of inputs."""

    def next(self, search=brute, inputs=iter, *args, **kwargs):
        # A brute-force, general approach is to yield all combinations
        # (n choose k for k in 1..n) of enabling events from all inputs.
        # We don't care about ordering (why we don't do permutations),
        # and there is no repetition.
        inputs = inputs(self.inputs)
        inputs_itr = itertools.imap(lambda x: x.next(*args, **kwargs), inputs)            
        for events in search(inputs_itr):
            # ignore empty events
            if len(events) == 0:
                continue
            yield events
            
#############################################################################
#############################################################################

class Demultiplexer(trellis.Component, circuit.Demultiplexer):

    input = trellis.attr(None)
    outputs = trellis.attr(None)
    
    @trellis.compute
    def next(self):
        return self.pass_in(self.input)


class Tee(Demultiplexer):
    """Copies an input to all outputs."""

    @trellis.modifier
    def send(self, input, outputs=iter, *args, **kwargs):
        outputs = outputs(self.outputs)
        for output in outputs:
            output.send(input, *args, **kwargs)
        
#############################################################################
#############################################################################
