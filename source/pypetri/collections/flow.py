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

class Aggregate(net.Pipe):

    def send(self, inputs, *args, **kwargs):
        # sum all inputs
        total = 0
        for input in inputs:
            total += input()
        super(Aggregate, self).send(total, *args, **kwargs)

#############################################################################
#############################################################################

class Gateway(net.Demultiplexer):

    predicate = trellis.attr(None)
    
    def __init__(self, predicate=None, *args, **kwargs):
        if predicate is None:
            predicate = lambda flow: bounded(flow, minimum=self.minimum, maximum=self.maximum)
        super(Gateway, self).__init__(*args, predicate=predicate, **kwargs)
        
    @trellis.maintain
    def minimum(self): # TODO: optimize?
        outputs = self.outputs
        if outputs is None:
            return None
        demand = 0
        for output in outputs:
            if not output.connected:
                continue
            output = output.output
            minimum = output.minimum
            if minimum:
                if output.marking:
                    minimum -= output.marking
                demand += minimum
        return demand
    
    @trellis.maintain
    def maximum(self): # TODO: optimize?
        outputs = self.outputs
        if outputs is None:
            return None
        demand = 0
        for output in outputs:
            if not output.connected:
                continue
            output = output.output
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
        for flows in super(Gateway, self).next(*args, **kwargs):
            inflow = sum([flow.args[0] for flow in flows])
            if predicate(inflow):
                yield flows

    @trellis.modifier
    def send(self, total, assigner=None, outputs=None):
        if outputs is None:
            outputs = [x for x in self.outputs if x.connected]
        if assigner is None:
            assigner = roundrobin
        
        assigned = {}
        
        # meet the minimums
        for x in outputs:
            minimum = x.output.minimum
            count = 0
            if minimum:
                count = minimum
            if count > total:
                raise RuntimeError(total)
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
            raise RuntimeError(total)
        
        # finally, send
        for x, count in assigned.iteritems():
            x.send(count)

#############################################################################
#############################################################################

class FlowNetwork(net.Network):

    @trellis.modifier
    def Condition(self, *args, **kwargs):
        condition = Counter(*args, **kwargs)
        self.conditions.add(condition)
        return condition
    
    @trellis.modifier
    def Transition(self, *args, **kwargs):
        if 'demux' not in kwargs:
            kwargs['demux'] = Gateway()
        if 'pipe' not in kwargs:
            kwargs['pipe'] = Aggregate()
        transition = net.Transition(*args, **kwargs)
        self.transitions.add(transition)
        return transition

#############################################################################
#############################################################################
    
Network = FlowNetwork

#############################################################################
#############################################################################
