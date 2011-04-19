# @copyright
# @license

import pypetri.trellis as trellis
import pypetri.net

#############################################################################
#############################################################################

class SimpleMarking(pypetri.net.Marking):

    count = trellis.attr(0)
    
    def __hash__(self):
        return hash(self.count)
    
    def __cmp__(self, other):
        if isinstance(other, self.__class__):
            return cmp(self.count, other.count)
        return cmp(self.count, other)

    def __add__(self, other):
        sum = self.count + other.count
        return self.__class__(count=sum)
    
    def __sub__(self, other):
        sum = self.count - other.count
        if sum < 0:
            raise ValueError(other)
        return self.__class__(count=sum)
    
    def __int__(self):
        return self.count
    
    def __nonzero__(self):
        return self.count > 0

#############################################################################
#############################################################################

class SimpleArc(pypetri.net.Arc):
    
    Marking = SimpleMarking
    
    demand = trellis.attr(None)
        
    def search(self):
        if self.source is None:
            return
        marking = self.source.marking
        demand = self.demand
        if marking >= demand:
            flow = self.Flow(arc=self, marking=demand,)
            yield flow
            
    def enabled(self, flow):
        return flow.marking == self.demand

#############################################################################
#############################################################################

class SimpleTransition(pypetri.net.Transition):
    
    @trellis.maintain
    def outflow(self):
        sum = 0
        if self.outputs is not None:
            outputs = [x.output.output for x in self.outputs if x.connected]
            for output in outputs:
                sum += int(output.demand)
        return sum
    
    def enabled(self, event):
        inflow = 0
        for flow in event.flows:
            inflow += int(flow.marking)
        return inflow == self.outflow
    
    def __call__(self, event):
        if not self.enabled(event):
            raise RuntimeError(event)
        outputs = self.Event(transition=self,)
        outgoing = [o.output.output for o in self.outputs if o.connected]
        for arc in outgoing:
            output = self.Flow(arc=arc, marking=arc.demand)
            outputs.add(output)
        return outputs

#############################################################################
#############################################################################
  
class SimpleCondition(pypetri.net.Condition):
    Marking = SimpleMarking
    
    def __init__(self, marking=None, **kwargs):
        if marking is None:
            marking = self.Marking()
        super(SimpleCondition, self).__init__(marking=marking, **kwargs)
    
    count = property(lambda self: self.marking.count)

#############################################################################
#############################################################################

class SimpleNetwork(pypetri.net.Network):

    Arc = SimpleArc
    Transition = SimpleTransition
    Condition = SimpleCondition

    def connect(self, source, sink, demand=None, **kwargs):
        if demand is None:
            demand = 1
        if isinstance(demand, int):
            demand = self.Arc.Marking(count=demand)
        return super(SimpleNetwork, self).connect(source, sink, demand=demand, **kwargs)
        
#############################################################################
#############################################################################
