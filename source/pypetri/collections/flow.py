# @copyright
# @license

from __future__ import absolute_import

import itertools

from . import trellis
from .. import net, operators

#############################################################################
#############################################################################

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

class Condition(net.Condition):

    marking = trellis.attr(initially=0)
    minimum = trellis.make(lambda self: None)
    maximum = trellis.make(lambda self: None)
    
    @trellis.maintain
    def bounded(self):
        # Enforce bounds
        marking = self.marking
        minimum = self.minimum
        maximum = self.maximum
        if not bounded(marking, minimum=minimum, maximum=maximum):
            raise ValueError(marking)
        return marking

    @trellis.modifier
    def send(self, count):
        total = self.marking + count
        self.marking = total
    
    @trellis.modifier
    def pull(self, count):
        total = self.marking - count
        self.marking = total
        return count
    
    def next(self, counter=None, *args, **kwargs):
        if counter is None:
            counter = self.Event(decreasing, minimum=self.minimum, maximum=self.maximum)
        Event = self.Event
        pull = self.pull
        for count in counter(self.marking, *args, **kwargs):
            event = Event(pull, count)
            yield event

#############################################################################
#############################################################################

class Transition(net.Transition):
    
    @classmethod
    def aggregate(cls, inputs):
        yield sum([i() for i in inputs])
    
    @classmethod
    def Pipe(cls):
        return operators.FilterOut(fn=cls.aggregate)

    class Demultiplexer(operators.Demultiplexer):
    
        predicate = trellis.attr(bounded)

        @trellis.compute
        def minimum(self): # TODO: optimize?
            outputs = self.outputs
            if not outputs:
                return None
            demand = 0
            for output in outputs:
                output = output.output
                if output is None:
                    continue
                minimum = output.minimum
                if minimum:
                    if output.marking:
                        minimum -= output.marking
                    demand += minimum
            return demand
        
        @trellis.compute
        def maximum(self): # TODO: optimize?
            outputs = self.outputs
            if not outputs:
                return None
            demand = 0
            for output in outputs:
                output = output.output
                if output is None:
                    continue
                maximum = output.maximum
                if maximum is None:
                    return None
                if maximum:
                    if output.marking:
                        maximum -= output.marking
                    demand += maximum
            return demand
    
        def next(self, *args, **kwargs):
            predicate = self.predicate
            minimum = self.minimum
            maximum = self.maximum
            for flows in super(Transition.Demultiplexer, self).next(*args, **kwargs):
                inflow = sum([flow.args[0] for flow in flows])
                if predicate(inflow, minimum, maximum):
                    yield flows
    
        @trellis.modifier
        def send(self, total, assigner=roundrobin, outputs=iter):
            outputs = [x for x in outputs(self.outputs) if x.output is not None]
            
            assigned = {}
            
            # meet the minimums
            for x in outputs:
                minimum = x.output.minimum
                count = 0
                if minimum:
                    count = minimum
                if count > total:
                    raise ValueError(total)
                total -= count
                assigned[x] = count
    
            # some policy to allocate the remainder
            capacities = {}
            for x in assigned:
                maximum = x.output.maximum
                capacity = maximum
                if capacity is not None:
                    capacity -= assigned[x]
                capacities[x] = capacity
            for x, count in assigner(total, capacities):
                assert count <= total
                total -= count
                assigned[x] += count
            
            if total != 0:
                raise ValueError(total)
            
            # finally, send
            for x, count in assigned.iteritems():
                x.send(count)

#############################################################################
#############################################################################

class FlowNetwork(net.Network):

    def Condition(self, Condition=Condition, *args, **kwargs):
        return super(FlowNetwork, self).Condition(Condition, *args, **kwargs)
    
    @trellis.modifier
    def Transition(self, Transition=Transition, *args, **kwargs):
        return super(FlowNetwork, self).Transition(Transition, *args, **kwargs)

#############################################################################
#############################################################################
    
Network = FlowNetwork

#############################################################################
#############################################################################
