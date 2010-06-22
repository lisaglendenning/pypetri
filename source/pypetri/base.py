
import warnings
warnings.simplefilter("ignore", DeprecationWarning)

from peak.events import trellis

import pypetri.hub as phub

#############################################################################
#############################################################################

class BaseRelation(phub.Connector):
    
    domains = trellis.make(tuple)
    
    def __init__(self, domains, **kwargs):
        super(BaseRelation, self).__init__(domains=domains, **kwargs)
    
    @trellis.modifier
    def bind(self, other):
        if not isinstance(other, BaseRelation):
            raise TypeError(self, other)
        if not issubclass(self.domains[0], other.domains[0]):
            raise TypeError(self, other)
        if not issubclass(other.domains[1], self.domains[1]):
            raise TypeError(self, other)
        super(BaseRelation, self).bind(other)
    
    @trellis.modifier
    def push(self, marking):
        self.superior.push(marking)

    @trellis.modifier
    def pull(self, marking):
        self.superior.pull(marking)
        
#############################################################################
#############################################################################
    
class BaseCondition(phub.Hub):
    
    marking = trellis.attr(None)
    
    clock = property(lambda self: self.superior.clock)
        
#############################################################################
#############################################################################

class BaseTransition(phub.Hub):
    
    clock = property(lambda self: self.superior.clock)
    
    def enabled(self):
        """Returns an iterator over a set of enabling Events."""
        pass
    
    def fire(self, event):
        """Returns an Event."""
        pass

#############################################################################
#############################################################################

class BaseArc(phub.Hub):
    
    clock = property(lambda self: self.superior.clock)
    
    domains = trellis.make(tuple)
    
    def __init__(self, domains, **kwargs):
        super(BaseArc, self).__init__(domains=domains, **kwargs)
    
    def traverse(self, index):
        return self.peerings[self.inferiors[str(index)].uid]

    def enabled(self):
        """Returns an iterator over a set of enabling Markings."""
        pass
    
    @trellis.modifier
    def push(self, marking):
        output = self.traverse(1)
        if not output:
            raise ValueError(marking)
        output = self.root.get(output[0])
        output.push(marking)
    
    @trellis.modifier
    def pull(self, marking):
        input = self.traverse(0)
        if not input:
            raise ValueError(marking)
        input = self.root.get(input[0])
        input.pull(marking)
    
#############################################################################
#############################################################################

class BaseMarking(trellis.Component):
    """Mapping of a hub to some tokens. """
    
    hub = trellis.make(None)
    timestamp = trellis.attr(0)

    def push(self, other):
        pass
    
    def pull(self, other):
        pass
    
    def disjoint(self, subs):
        pass

#############################################################################
#############################################################################

class BaseEvent(trellis.Component):
    
    transition = trellis.make(None)
    
    def __init__(self, *args, **kwargs):
        super(BaseEvent, self).__init__(*args, **kwargs)
        self.markings = { }

    def add(self, other):
        uid = other.hub.uid
        self.markings[uid] = other
    
    def remove(self, other):
        uid = other.hub.uid
        del self.markings[uid]

#############################################################################
#############################################################################

class BaseDeclarations(object):

    ROLES = []

#############################################################################
#############################################################################

class BaseCollective(phub.Hub):

    declarations = trellis.make(None)

    def __init__(self, declarations, **kwargs):
        if 'clock' not in kwargs:
            kwargs['clock'] = 0
        super(BaseCollective, self).__init__(declarations=declarations, **kwargs)
        self.roles = {}
        for role in self.declarations.ROLES:
            self.roles[role] = trellis.Set()

    @trellis.modifier
    def Arc(self, *args, **kwargs):
        arc = self.declarations.Arc(*args, **kwargs)
        cin = self.declarations.Relation(domains=(arc.domains[0], arc.__class__), name='0')
        cout = self.declarations.Relation(domains=(arc.__class__, arc.domains[1]), name='1')
        arc.add(cin)
        arc.add(cout)
        return arc
    
    def is_actor(self, uid, role):
        hub = self.get(uid)
        name = hub.name
        for r in self.roles:
            if name in self.roles[r]:
                if issubclass(r, role):
                    return True
        return False
    
    def actors(self, role):
        for r in self.roles:
            if issubclass(r, role):
                actors = set([self.inferiors[name].uid for name in self.roles[r]])
                return actors
        raise KeyError(self, role)
    
    @trellis.maintain
    def classify(self):
        changes = self.inferiors.added
        if changes:
            for inferior in changes.itervalues():
                for role in self.declarations.ROLES:
                    if isinstance(inferior, role):
                        self.roles[role].add(inferior.name)
                        break
        changes = self.inferiors.deleted
        if changes:
            for inferior in changes.itervalues():
                for role in self.declarations.ROLES:
                    if isinstance(inferior, role):
                        self.roles[role].remove(inferior.name)
                        break
    
    @trellis.modifier
    def connect(self, arc, connectors):
        self.disconnect(arc)
        for i in (0, 1):
            arcc = arc.find(str(i))
            arcc.bind(connectors[i])
            connectors[i].bind(arcc)
    
    @trellis.modifier
    def disconnect(self, arc):
        for i in (0, 1):
            arcc = arc.find(str(i))
            peer = arcc.peer
            if peer:
                peer.unbind()
                arcc.unbind()
    
    def marking(self, uid):
        if not self.is_sub(uid):
            raise ValueError(uid)
        if not self.is_actor(uid, self.declarations.Condition):
            raise TypeError(uid)
        condition = self.get(uid)
        return condition.marking

    def disjoint(self, events):
        # find shared input conditions
        inputs = { }
        for event in events:
            for marking in event.markings.itervalues():
                arc = marking.hub
                path = arc.traverse(0)
                if path is None:
                    raise ValueError(arc)
                uid = path[1]
                if self.is_actor(uid, self.declarations.Condition):
                    if uid not in inputs:
                        inputs[uid] = []
                    inputs[uid].append(marking)
        for uid, markings in inputs.iteritems():
            if len(markings) < 2:
                continue
            superset = self.marking(uid)
            if not superset.disjoint(markings):
                return False
        return True    
    
    @trellis.modifier
    def step(self, events):
        inevents = []
        outevents = []
        for inevent in events:
            inevents.append(inevent)
            outevent = inevent.transition.fire(inevent)
            outevents.append(outevent)
        for event in inevents:
            for marking in event.markings.itervalues():
                arc = marking.hub
                arc.pull(marking)
        for event in outevents:
            for marking in event.markings.itervalues():
                arc = marking.hub
                arc.push(marking)
    
    @trellis.maintain
    def clock(self):
        clock = self.clock
        for cond in self.actors(self.declarations.Condition):
            marking = self.marking(cond)
            if marking.timestamp > clock:
                clock = marking.timestamp
        return clock

#############################################################################
#############################################################################
