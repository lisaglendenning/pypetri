# @copyright
# @license

from __future__ import absolute_import

from . import trellis
from .. import net

#############################################################################
#############################################################################

Flow = int

def bounded(count, minimum=None, maximum=None):
        return (count is not None) and (minimum is None or count >= minimum)\
          and (maximum is None or count <= maximum)
        
def decreasing(count, minimum=None, maximum=None, step=-1):
        stop = 0 if minimum is None else minimum
        start = count if maximum is None else min(maximum, count)
        for i in xrange(start, stop, step):
            yield i
    
def increasing(count, minimum=None, maximum=None, step=1):
        start = 0 if minimum is None else minimum
        stop = count if maximum is None else min(maximum, count)
        for i in xrange(start, stop, step):
            yield i

def roundrobin(total, capacities):
    for x in capacities:
        if not total:
            break
        capacity = capacities[x]
        if capacity is None:
            capacity = total
        else:
            capacity = min(total, capacity)
        total -= capacity
        yield x, capacity
           
#############################################################################
#############################################################################

class Bounded(net.Arc):
     
    @trellis.maintain
    def minimum(self):
        output = self.output
        if isinstance(output, Counter):
            minimum = output.minimum
            if minimum:
                minimum = minimum - output.marking
            return minimum
    
    @trellis.maintain
    def maximum(self):
        output = self.output
        if isinstance(output, Counter):
            maximum = output.maximum
            if maximum:
                maximum = maximum - output.marking
            return maximum

#############################################################################
#############################################################################

class Counter(net.Condition):

    minimum = trellis.make()
    maximum = trellis.make()
    
    def __init__(self, *args, **kwargs):
        for k, v in (('marking', 0), ('minimum', None), ('maximum', None),):
            kwargs.setdefault(k, v)
        super(Counter, self).__init__(*args, **kwargs)
    
    @trellis.maintain
    def bounded(self):
        count = self.marking
        minimum = self.minimum
        maximum = self.maximum
        if not bounded(count, minimum=minimum, maximum=maximum):
            raise ValueError(count)
        return True

    @trellis.modifier
    def send(self, count):
        total = self.marking + count
        self.marking = total
        return count
    
    @trellis.modifier
    def pull(self, count):
        total = self.marking - count
        self.marking = total
        return count
    
    def next(self, counter=None, *args, **kwargs):
        if counter is None:
            counter = self.Event(decreasing, minimum=self.minimum, maximum=self.maximum)
        for count in counter(self.marking, *args, **kwargs):
            event = self.Event(self.pull, count)
            yield event

#############################################################################
#############################################################################

class Threshold(net.Serializer):

    predicate = trellis.attr(None)
    
    def __init__(self, predicate=None, *args, **kwargs):
        if predicate is None:
            predicate = lambda flow: bounded(flow, minimum=self.minimum, maximum=self.maximum)
        super(Threshold, self).__init__(*args, predicate=predicate, **kwargs)

    @trellis.compute
    def minimum(self):
        try:
            return self.output.minimum
        except AttributeError:
            return None

    @trellis.compute
    def maximum(self):
        try:
            return self.output.maximum
        except AttributeError:
            return None
        
    def next(self, *args, **kwargs):
        predicate = self.predicate
        for event in super(Threshold, self).next(*args, **kwargs):
            flows = event.keywords['inputs']
            inflow = sum([flow.args[0] for flow in flows])
            if predicate(inflow):
                kw = dict(event.keywords)
                kw['input'] = kw['inputs']
                del kw['inputs']
                yield event.__class__(event.func, *event.args, **kw)

class Sum(net.Pipe):
    
    @trellis.compute
    def minimum(self):
        try:
            return self.output.minimum
        except AttributeError:
            return None

    @trellis.compute
    def maximum(self):
        try:
            return self.output.maximum
        except AttributeError:
            return None
        
    def send(self, inputs, *args, **kwargs):
        # sum all inputs
        total = 0
        for input in inputs:
            total += input()
        super(Sum, self).send(total, *args, **kwargs)

class Assign(net.Demultiplexer):

    @trellis.maintain
    def minimum(self): # FIXME: optimize
        outputs = self.outputs
        if not outputs:
            return None
        bounds = [x.minimum for x in outputs if x.connected]
        bounds = [x for x in bounds if x is not None]
        demand = sum(bounds)
        return demand
    
    @trellis.maintain
    def maximum(self): # FIXME: optimize
        outputs = self.outputs
        if not outputs:
            return None
        bounds = [x.maximum for x in outputs if x.connected]
        if None in bounds:
            demand = None
        else:
            demand = sum(bounds)
        return demand

    @trellis.modifier
    def send(self, total, assigner=None, outputs=None):
        if outputs is None:
            outputs = [x for x in self.outputs if x.connected]
        if assigner is None:
            assigner = roundrobin
        
        assigned = {}
        
        # meet the minimums
        for x in outputs:
            if not x.minimum:
                count = 0
            elif x.minimum > total:
                raise RuntimeError(total)
            else:
                count = x.minimum
                total -= count
            assigned[x] = count

        # some policy to allocate the remainder
        capacities = {}
        for x in assigned:
            capacity = x.maximum
            if capacity is not None:
                capacity -= assigned[x]
            capacities[x] = capacity
        for x, count in assigner(total, capacities):
            assigned[x] += count
        
        # finally, send
        for x, count in assigned.iteritems():
            total -= x.send(count)
        return total
    
#############################################################################
#############################################################################

class Conserve(net.Transition):
    r"""Conserves total flow from inputs to outputs."""
    
    def __init__(self, *args, **kwargs):
        if 'mux' not in kwargs:
            kwargs['mux'] = Threshold()
        if 'pipe' not in kwargs:
            kwargs['pipe'] = Sum()
        if 'demux' not in kwargs:
            kwargs['demux'] = Assign()
        super(Conserve, self).__init__(*args, **kwargs)


#############################################################################
#############################################################################

class FlowNetwork(net.Network):

    Arc = Bounded
    Transition = Conserve
    Condition = Counter
    
Network = FlowNetwork

#############################################################################
#############################################################################
