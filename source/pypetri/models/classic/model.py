import warnings
warnings.simplefilter("ignore", DeprecationWarning)

from peak.events import trellis

import pypetri.base as pbase

#############################################################################
#############################################################################

class ClassicMarking(pbase.BaseMarking):

    count = trellis.attr(0)

    def push(self, other):
        self.count += other.count
        if other.timestamp >= self.timestamp:
            self.timestamp = other.timestamp + 1
    
    def pull(self, other):
        assert self.count >= other.count
        self.count -= other.count
        if other.timestamp >= self.timestamp:
            self.timestamp = other.timestamp + 1
    
    def disjoint(self, subs):
        sum = reduce(lambda x,y: x.count + y.count, subs)
        return sum <= self.count

#############################################################################
#############################################################################

class ClassicArc(pbase.BaseArc):
    
    capacity = trellis.make(int)

    def __init__(self, capacity=1, *args, **kwargs):
        super(ClassicArc, self).__init__(*args, capacity=capacity, **kwargs)
        
    def enabled(self):
        input = self.traverse(0)
        if not input:
            return
        puid = input[1]
        if not self.superior.is_actor(puid, Declarations.Condition):
            return
        pmarks = self.superior.marking(puid)
        if pmarks.count >= self.capacity:
            marks = self.superior.declarations.Marking(hub=self, 
                                                       count=self.capacity,
                                                       timestamp=pmarks.timestamp)
            yield marks
        return

#############################################################################
#############################################################################

class ClassicTransition(pbase.BaseTransition):
    
    def enabled(self):
        event = pbase.BaseEvent(transition=self)
        for path in self.peerings.itervalues():
            if not path:
                continue
            uid = path[1]
            arc = self.superior.get(uid)
            if not isinstance(self, arc.domains[1]):
                continue
            arciter = arc.enabled()
            try:
                event.add(arciter.next())
            except StopIteration:
                return
        if len(event.markings):
            yield event
        return
    
    def fire(self, inevent):
        outevent = pbase.BaseEvent(transition=self)
        available = reduce(lambda x,y: x+y, [m.count for m in inevent.markings.itervalues()])
        timestamp = reduce(lambda x,y: max(x,y), [m.timestamp for m in inevent.markings.itervalues()])
        for path in self.peerings.itervalues():
            if not path:
                continue
            uid = path[1]
            arc = self.superior.get(uid)
            if not isinstance(self, arc.domains[0]):
                continue
            if available < arc.capacity:
                raise ValueError(self)
            marks = self.superior.declarations.Marking(hub=arc, 
                                                       count=arc.capacity,
                                                       timestamp=timestamp)
            available -= marks.count
            outevent.markings[uid] = marks
        if available != 0:
            raise ValueError(self)
        return outevent

#############################################################################
#############################################################################
  
class ClassicCondition(pbase.BaseCondition):
    
    def __init__(self, *args, **kwargs):
        marking = Declarations.Marking(hub=self)
        super(ClassicCondition, self).__init__(*args, marking=marking, **kwargs)

    @trellis.modifier
    def push(self, other):
        self.marking.push(other)
    
    @trellis.modifier
    def pull(self, other):
        self.marking.pull(other)
            
#############################################################################
#############################################################################

class Declarations(pbase.BaseDeclarations):
    
    Condition = ClassicCondition
    Transition = ClassicTransition
    Arc = ClassicArc
    Marking = ClassicMarking
    Relation = pbase.BaseRelation
    
Declarations.ROLES = [Declarations.Condition, Declarations.Transition, Declarations.Arc]

#############################################################################
#############################################################################
  
class ClassicCollective(pbase.BaseCollective):
    
    ARC_TOKEN = "->"
    
    def __init__(self, declarations=Declarations, **kwargs):
        super(ClassicCollective, self).__init__(declarations=declarations, **kwargs)

    def create_arc(self, hubs, capacity=1):
        names = [h.name for h in hubs]
        domains = [h.__class__ for h in hubs]
        name = self.ARC_TOKEN.join(names)
        arc = self.Arc(name=name, domains=domains, capacity=capacity)
        self.add(arc)
        connectors = [self.declarations.Relation(name=arc.name, domains=(domains[0], arc.__class__)),
                      self.declarations.Relation(name=arc.name, domains=(arc.__class__, domains[1])),]
        for i in xrange(len(hubs)):
            hubs[i].add(connectors[i])
        self.connect(arc, connectors)
    
#############################################################################
#############################################################################
