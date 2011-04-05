# @copyright
# @license

import collections

import pypetri.trellis as trellis
import pypetri.hierarchy

#############################################################################
#############################################################################

class Relation(pypetri.hierarchy.Connector):
    
    @trellis.modifier
    def connect(self, other):
        if not issubclass(self.types[0], other.types[0]):
            raise TypeError(other)
        if not issubclass(other.types[1], self.types[1]):
            raise TypeError(other)
        super(Relation, self).connect(other)
        
    types = trellis.make(tuple)
    
    def __init__(self, types, **kwargs):
        super(Relation, self).__init__(types=types, **kwargs)

#############################################################################
#############################################################################

class Arc(pypetri.hierarchy.Composer):
    
    NAME_IN = '0'
    NAME_OUT = '1'
    
    Relation = Relation
    
    types = trellis.make(tuple)
    
    @classmethod
    @trellis.modifier
    def create(cls, *args, **kwargs):
        arc = cls(*args, **kwargs)
        input = arc.Relation(types=(arc.types[0], cls), name=arc.NAME_IN)
        output = arc.Relation(types=(cls, arc.types[1]), name=arc.NAME_OUT)
        arc.add(input)
        arc.add(output)
        return arc
    
    def __init__(self, types, **kwargs):
        super(Arc, self).__init__(types=types, **kwargs)
    
    @trellis.maintain
    def input(self):
        name = self.NAME_IN
        if name in self:
            return self[name]
        else:
            return None
    
    @trellis.maintain
    def output(self):
        name = self.NAME_OUT
        if name in self:
            return self[name]
        else:
            return None
    
    @trellis.maintain
    def source(self):
        input = self.input
        if input is not None and input.connected:
            return input.peer.domain
        return None    

    @trellis.maintain
    def sink(self):
        output = self.output
        if output is not None and output.connected:
            return output.peer.domain
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

class Vertex(pypetri.hierarchy.Composer):
    
    Relation = Relation
    
    def __init__(self, *args, **kwargs):
        super(Vertex, self).__init__(*args, **kwargs)
        self.inputs = trellis.Set()
        self.outputs = trellis.Set()
    
    @trellis.modifier
    def add(self, inferior):
        if not isinstance(inferior, self.Relation):
            raise TypeError(inferior)
        if not (isinstance(self, inferior.types[0]) \
                or isinstance(self, inferior.types[1])):
            raise TypeError(inferior)
        return super(Vertex, self).add(inferior)
    
    @trellis.maintain
    def classify(self):
        changes = self.contains.added
        if changes:
            for relation in changes.itervalues():
                if isinstance(self, relation.types[0]):
                    self.outputs.add(relation)
                else:
                    self.inputs.add(relation)
        changes = self.contains.deleted
        if changes:
            for relation in changes.itervalues():
                if isinstance(self, relation.types[0]):
                    self.outputs.remove(relation)
                else:
                    self.inputs.remove(relation)

        
#############################################################################
#############################################################################

class Condition(Vertex):
    
    marking = trellis.attr(None)
    
        
#############################################################################
#############################################################################

class Transition(collections.Callable, Vertex):
    
    def enabled(self):
        """Returns an iterator over a set of enabling Events."""
        pass
    
    def __call__(self, event):
        """Returns an Event."""
        pass

#############################################################################
#############################################################################

class Marking(trellis.Component):
    """Mapping of a component to some tokens. """
    
    marks = trellis.make(None)

    def push(self, other):
        pass
    
    def pull(self, other):
        pass
    
    def disjoint(self, subs):
        pass

#############################################################################
#############################################################################

class Event(collections.Callable):
    
    def __init__(self, transition):
        self.transition = transition
        self.markings = set()

    def __call__(self):
        return self.transition.fire(self)

#############################################################################
#############################################################################

class Network(pypetri.hierarchy.Composer):
    
    Arc = Arc
    Condition = Condition
    Transition = Transition

    def disjoint(self, events):
        # find shared input conditions
        inputs = { }
        for event in events:
            for marking in event.markings:
                arc = marking.marks
                source = arc.source
                if source.uid not in inputs:
                    inputs[source.uid] = source.marking, []
                inputs[source.uid][1].append(marking)
        for superset, markings in inputs.itervalues():
            if len(markings) < 2:
                continue
            if not superset.disjoint(markings):
                return False
        return True    
    
    @trellis.modifier
    def step(self, events):
        for event in events:
            self.trigger(event)
    
    @trellis.modifier
    def trigger(self, input):
        output = input()
        for marking in input.markings:
            arc = marking.marks
            arc.pull(marking)
        for marking in output.markings:
            arc = marking.marks
            arc.push(marking)
        return output

#############################################################################
#############################################################################
