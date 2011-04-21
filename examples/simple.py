# @copyright
# @license

import pypetri.trellis as trellis
import pypetri.net

#############################################################################
#############################################################################

class Count(pypetri.net.Marking):

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

class Threshold(pypetri.net.Port):

    demand = trellis.attr(None)
        
    def peek(self):
        demand = self.demand
        for flow in super(Threshold, self).peek():
            if flow.marking >= demand:
                flow.marking = demand
                yield flow
    
    def __int__(self):
        demand = 0 if self.demand is None else int(self.demand)
        return demand

#############################################################################
#############################################################################

class Conserve(pypetri.net.Transition):
    
    Port = Threshold
    
    @trellis.maintain
    def demands(self):
        if self.outputs is None:
            return set()
        ports = [x for x in self.outputs if x.connected]
        return ports
    
    @trellis.maintain
    def outflow(self):
        outflow = 0
        for threshold in self.demands:
            outflow += int(threshold)
        return outflow
    
    def peek(self, *args):
        for event in super(Conserve, self).peek(*args):
            inflow = 0
            for flow in event.flows:
                inflow += int(flow.marking)
            if inflow == self.outflow:
                yield event
    
    def __call__(self, event):
        outputs = self.Event(transition=self,)
        for threshold in self.demands:
            arc = threshold.output.output
            output = self.Flow(arc=arc, marking=threshold.demand)
            outputs.add(output)
        return outputs

#############################################################################
#############################################################################
  
class Tokens(pypetri.net.Condition):
    Marking = Count
    
    def __init__(self, marking=None, **kwargs):
        if marking is None:
            marking = self.Marking()
        super(Tokens, self).__init__(marking=marking, **kwargs)
    
    count = property(lambda self: self.marking.count)

#############################################################################
#############################################################################

class TokenNetwork(pypetri.net.Network):

    Transition = Conserve
    Condition = Tokens

    def connect(self, source, sink, arc=None, demand=None, **kwargs):
        if demand is None:
            demand = 1
        if isinstance(demand, int):
            demand = self.Condition.Marking(count=demand)
        names = (source.uid, sink.uid,)
        name = self.ARC_TOKEN.join(names)
        if pypetri.net.instantiates(source, self.Transition):
            source = self.open(source, name, input=False, demand=demand)
        if pypetri.net.instantiates(sink, self.Transition):
            sink = self.open(sink, name, input=True, demand=demand)
        return super(TokenNetwork, self).connect(source, sink, **kwargs)
        
#############################################################################
#############################################################################
