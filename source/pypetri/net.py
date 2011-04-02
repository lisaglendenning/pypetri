# @copyright
# @license

import pypetri.trellis as trellis
import pypetri.hub

#############################################################################
#############################################################################

class Relation(pypetri.hub.Connector):
    
    @trellis.modifier
    def connect(self, other):
        if not issubclass(self.domains[0], other.domains[0]):
            raise TypeError(other)
        if not issubclass(other.domains[1], self.domains[1]):
            raise TypeError(other)
        super(Relation, self).connect(other)
        
    domains = trellis.make(tuple)
    
    def __init__(self, domains, **kwargs):
        super(Relation, self).__init__(domains=domains, **kwargs)

#############################################################################
#############################################################################

class Arc(pypetri.hub.Hub):
    
    NAME_IN = '0'
    NAME_OUT = '1'
    
    Relation = Relation
    
    domains = trellis.make(tuple)
    
    @classmethod
    @trellis.modifier
    def create(cls, *args, **kwargs):
        arc = cls(*args, **kwargs)
        input = arc.Relation(domains=(arc.domains[0], cls), name=arc.NAME_IN)
        output = arc.Relation(domains=(cls, arc.domains[1]), name=arc.NAME_OUT)
        arc.add(input)
        arc.add(output)
        return arc
    
    def __init__(self, domains, **kwargs):
        super(Arc, self).__init__(domains=domains, **kwargs)
    
    @trellis.maintain
    def input(self):
        if self.NAME_IN in self.inferiors:
            return self.inferiors[self.NAME_IN]
        else:
            return None
    
    @trellis.maintain
    def output(self):
        if self.NAME_OUT in self.inferiors:
            return self.inferiors[self.NAME_OUT]
        else:
            return None
    
    @trellis.maintain
    def source(self):
        input = self.input
        if input is not None and input.connected:
            return input.peer.superior
        return None    

    @trellis.maintain
    def sink(self):
        output = self.output
        if output is not None and output.connected:
            return output.peer.superior
        return None
    
    @trellis.modifier
    def push(self, marking):
        if not self.sink:
            raise RuntimeError(marking)
        return self.sink.push(marking)
    
    @trellis.modifier
    def pull(self, marking):
        if not self.source:
            raise RuntimeError(marking)
        return self.source.pull(marking)
                
    def enabled(self):
        """Returns an iterator over a set of enabling Markings."""
        pass

#############################################################################
#############################################################################

class Vertex(pypetri.hub.Hub):
    
    Relation = Relation
    
    def __init__(self, *args, **kwargs):
        super(Vertex, self).__init__(*args, **kwargs)
        self.inputs = trellis.Set()
        self.outputs = trellis.Set()
    
    @trellis.modifier
    def add(self, inferior):
        if not isinstance(inferior, self.Relation):
            raise TypeError(inferior)
        if not (isinstance(self, inferior.domains[0]) \
                or isinstance(self, inferior.domains[1])):
            raise TypeError(inferior)
        return super(Vertex, self).add(inferior)
    
    @trellis.maintain
    def classify(self):
        changes = self.inferiors.added
        if changes:
            for relation in changes.itervalues():
                if isinstance(self, relation.domains[0]):
                    self.outputs.add(relation)
                else:
                    self.inputs.add(relation)
        changes = self.inferiors.deleted
        if changes:
            for relation in changes.itervalues():
                if isinstance(self, relation.domains[0]):
                    self.outputs.remove(relation)
                else:
                    self.inputs.remove(relation)

        
#############################################################################
#############################################################################

class Condition(Vertex):
    
    marking = trellis.attr(None)
    
        
#############################################################################
#############################################################################

class Transition(Vertex):
    
    def enabled(self):
        """Returns an iterator over a set of enabling Events."""
        pass
    
    def fire(self, event):
        """Returns an Event."""
        pass

#############################################################################
#############################################################################

class Marking(trellis.Component):
    """Mapping of a hub to some tokens. """
    
    hub = trellis.make(None)

    def push(self, other):
        pass
    
    def pull(self, other):
        pass
    
    def disjoint(self, subs):
        pass

#############################################################################
#############################################################################

class Event(object):
    
    def __init__(self, transition):
        self.transition = transition
        self.markings = set()

    def fire(self):
        return self.transition.fire(self)

#############################################################################
#############################################################################

class Network(pypetri.hub.Hub):

    def disjoint(self, events):
        # find shared input conditions
        inputs = { }
        for event in events:
            for marking in event.markings:
                arc = marking.hub
                source = arc.source
                if source.uid not in inputs:
                    inputs[source.uid] = []
                inputs[source.uid].append(marking)
        for uid, markings in inputs.iteritems():
            if len(markings) < 2:
                continue
            if self.is_superior(uid):
                uid = uid.split(self.SUB_TOKEN, 1)[1]
            superset = self.find(uid).marking
            if not superset.disjoint(markings):
                return False
        return True    
    
    @trellis.modifier
    def step(self, events):
        for event in events:
            self.trigger(event)
    
    @trellis.modifier
    def trigger(self, input):
        output = input.fire()
        for marking in input.markings:
            arc = marking.hub
            arc.pull(marking)
        for marking in output.markings:
            arc = marking.hub
            arc.push(marking)
        return output

#############################################################################
#############################################################################
