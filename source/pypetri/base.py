
import warnings
warnings.simplefilter("ignore", DeprecationWarning)

from peak.events import trellis

import pypetri.hub as phub

#############################################################################
#############################################################################

class Relation(phub.Connector):
    
    domains = trellis.make(tuple)
    
    def __init__(self, domains, **kwargs):
        super(Relation, self).__init__(domains=domains, **kwargs)
    
    @trellis.modifier
    def bind(self, other):
        if not isinstance(other, Relation):
            raise TypeError(self, other)
        if not issubclass(self.domains[0], other.domains[0]):
            raise TypeError(self, other)
        if not issubclass(other.domains[1], self.domains[1]):
            raise TypeError(self, other)
        super(Relation, self).bind(other)

#############################################################################
#############################################################################
    
class BaseCondition(phub.Hub):
    pass
        
#############################################################################
#############################################################################

class BaseTransition(phub.Hub):
    
    def enabled(self):
        """Returns an iterator over a set of enabling Events."""
        pass
    
    def fire(self, event):
        """Returns an Event."""
        pass

#############################################################################
#############################################################################

class BaseArc(phub.Hub):
    
    domains = trellis.make(tuple)
    
    def __init__(self, domains, **kwargs):
        super(BaseArc, self).__init__(domains=domains, **kwargs)
    
    def traverse(self, index):
        return self.peerings[self.inferiors[str(index)].uid]

    def enabled(self):
        """Returns an iterator over a set of enabling Markings."""
        pass
    
#############################################################################
#############################################################################

class BaseMarking(trellis.Component):
    """Mapping of a hub to some tokens. """
    
    hub = trellis.make(None)

    def add(self, other):
        pass
    
    def remove(self, other):
        pass
    
    def disjoint(self, subs):
        pass

#############################################################################
#############################################################################

class Event(trellis.Component):
    
    transition = trellis.make(None)
    
    def __init__(self, *args, **kwargs):
        super(Event, self).__init__(*args, **kwargs)
        self.markings = { }

    def add(self, other):
        uid = other.hub.uid
        self.markings[uid] = other
    
    def remove(self, other):
        uid = other.hub.uid
        del self.markings[uid]

#############################################################################
#############################################################################

class Declarations(object):

    ROLES = []

#############################################################################
#############################################################################

class Collective(phub.Hub):
    
    clock = trellis.attr(0)
    declarations = trellis.make(None)

    def __init__(self, **kwargs):
        super(Collective, self).__init__(**kwargs)
        self.markings = trellis.Dict()
        self.roles = {}
        for role in self.declarations.ROLES:
            self.roles[role] = trellis.Set()

    @trellis.modifier
    def Arc(self, *args, **kwargs):
        arc = self.declarations.Arc(*args, **kwargs)
        cin = Relation(domains=(arc.domains[0], arc.__class__), name='0')
        cout = Relation(domains=(arc.__class__, arc.domains[1]), name='1')
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
                        if issubclass(role, BaseCondition):
                            self.markings[inferior.name] = self.declarations.Marking(hub=inferior)
                        break
        changes = self.inferiors.deleted
        if changes:
            for inferior in changes.itervalues():
                for role in self.declarations.ROLES:
                    if isinstance(inferior, role):
                        self.roles[role].remove(inferior.name)
                        if issubclass(role, BaseCondition):
                            del self.markings[inferior.name]
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
        condition = self.get(uid)
        return self.markings[condition.name]

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
                if self.is_actor(uid, BaseCondition):
                    pname = self.get(uid).name
                    if pname not in inputs:
                        inputs[pname] = []
                    inputs[pname].append(marking)
        for pname, markings in inputs.iteritems():
            if len(markings) < 2:
                continue
            superset = self.markings[pname]
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
                path = arc.traverse(0)
                if path is None:
                    raise ValueError(arc)
                pmarking = self.marking(path[1])
                pmarking.remove(marking)
        for event in outevents:
            for marking in event.markings.itervalues():
                arc = marking.hub
                path = arc.traverse(1)
                if path is None:
                    raise ValueError(arc)
                pmarking = self.marking(path[1])
                pmarking.add(marking)
        self.tick()
    
    @trellis.modifier
    def tick(self):
        self.clock += 1
                
#############################################################################
#############################################################################
