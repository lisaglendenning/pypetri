# @copyright
# @license

import pypetri.trellis as trellis
import pypetri.net

#############################################################################
#############################################################################

class SimpleMarking(pypetri.net.Marking):

    count = trellis.attr(0)

    def push(self, other):
        self.count += other.count
    
    def pull(self, other):
        if other.count > self.count:
            raise RuntimeError(other)
        self.count -= other.count
    
    def disjoint(self, subs):
        sum = reduce(lambda x,y: x.count + y.count, subs)
        return sum <= self.count

#############################################################################
#############################################################################

class SimpleArc(pypetri.net.Arc):
    
    capacity = trellis.make(int)

    def __init__(self, capacity=1, **kwargs):
        super(SimpleArc, self).__init__(capacity=capacity, **kwargs)
        
    def enabled(self):
        if self.source is None:
            return
        source = self.source.marking
        if source.count >= self.capacity:
            marks = SimpleMarking(marks=self, count=self.capacity)
            yield marks
        return

#############################################################################
#############################################################################

class SimpleTransition(pypetri.net.Transition):
    
    def enabled(self):
        event = pypetri.net.Event(transition=self)
        for input in self.inputs:
            if not input.connected:
                continue
            arc = input.peer.domain
            arciter = arc.enabled()
            try:
                event.markings.add(arciter.next())
            except StopIteration:
                break
        else:
            if len(event.markings):
                yield event
    
    def fire(self, event):
        out = pypetri.net.Event(transition=self)
        available = reduce(lambda x,y: x+y, [m.count for m in event.markings])
        for output in self.outputs:
            if not output.connected:
                continue
            arc = output.peer.domain
            if available < arc.capacity:
                raise RuntimeError(event)
            marks = SimpleMarking(marks=arc, count=arc.capacity)
            available -= marks.count
            out.markings.add(marks)
        if available != 0:
            raise RuntimeError(event)
        return out

#############################################################################
#############################################################################
  
class SimpleCondition(pypetri.net.Condition):
    
    def __init__(self, **kwargs):
        marking = SimpleMarking(marks=self)
        super(SimpleCondition, self).__init__(marking=marking, **kwargs)

    @trellis.modifier
    def push(self, other):
        self.marking.push(other)
    
    @trellis.modifier
    def pull(self, other):
        self.marking.pull(other)
            
#############################################################################
#############################################################################

class SimpleNetwork(pypetri.net.Network):
    
    ARC_TOKEN = '->'

    Arc = SimpleArc
    Transition = SimpleTransition
    Condition = SimpleCondition

    def connect(self, source, sink, capacity=1):
        names = (source.uid, sink.uid,)
        types = []
        for cls in source.__class__, sink.__class__:
            for t in self.Condition, self.Transition:
                if issubclass(cls, t):
                    types.append(t)
                    break
        types = tuple(types)
        name = self.ARC_TOKEN.join(names)
        arc = self.Arc.create(name=name, 
                              types=types, 
                              capacity=capacity)
        self.add(arc)
        connectors = [arc.Relation(name=arc.name, types=(types[0], self.Arc)),
                      arc.Relation(name=arc.name, types=(self.Arc, types[1])),]
        source.add(connectors[0])
        sink.add(connectors[1])
        arc.input.connect(connectors[0])
        arc.output.connect(connectors[1])
        return arc

#############################################################################
#############################################################################
