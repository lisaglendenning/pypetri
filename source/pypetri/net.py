# @copyright
# @license

# TODO: could probably improve the code using itertools?

import collections

import pypetri.trellis as trellis
import pypetri.hierarchy

#############################################################################
#############################################################################

instantiates = isinstance

def brute(itr):
    """Brute force search of all variable-length combinations."""
    def recursor(itr):
        try:
            next = itr.next()
        except StopIteration:
            pass
        else:
            rest = recursor(itr)
            for combo in rest:
                for item in next:
                    yield [item] + combo
        finally:
            yield []
    for combo in recursor(itr):
        yield combo


def update(current, changes, filter=None):
    if filter is None:
        filter = lambda x: True
    added = set([x for x in changes.added.itervalues() if filter(x)])
    removed = current & set(changes.deleted)
    result = (current - removed) | added
    return result 
    
#############################################################################
#############################################################################

class Relation(object):
    """A relation is an ordered pair of types."""

    INPUT, OUTPUT = xrange(2)
    
    @classmethod
    def typecheck(cls, left, right):
        if not issubclass(left.types[left.INPUT], right.types[right.INPUT]):
            raise TypeError(right)
        if not issubclass(right.types[right.OUTPUT], left.types[left.OUTPUT]):
            raise TypeError(right)
    
    def __init__(self, *types):
        if len(types) !=  2:
            raise TypeError(types)
        self.types = tuple(types)
    
    input = None
    output = None
    
    @trellis.modifier
    def __lshift__(self, event):
        if self.output is None:
            raise RuntimeError(event)
        return self.output << event

    @trellis.modifier
    def __rshift__(self, event):
        if self.input is None:
            raise RuntimeError(event)
        return self.input >> event

#############################################################################
#############################################################################

class Port(Relation, pypetri.hierarchy.Connector):
    """A Port is a typed and directional connector between Petri Net components."""
    
    @classmethod
    def typecheck(cls, left, right):
        if left.domain is left.input:
            return Relation.typecheck(left, right)
        else:
            return Relation.typecheck(right, left)
    
    def __init__(self, *types, **kwargs):
        Relation.__init__(self, *types)
        pypetri.hierarchy.Connector.__init__(self, **kwargs)

    @trellis.modifier
    def connect(self, other):
        self.typecheck(self, other)
        pypetri.hierarchy.Connector.connect(self, other)

    @trellis.maintain
    def input(self): # FIXME: DRY
        type = self.types[self.INPUT]
        if self.domain is not None:
            if instantiates(self.domain, type):
                return self.domain
        if self.peer is not None and self.peer.domain is not None:
            if instantiates(self.peer.domain, type):
                return self.peer
        return None
    
    @trellis.maintain
    def output(self): # FIXME: DRY
        type = self.types[self.OUTPUT]
        if self.domain is not None:
            if instantiates(self.domain, type):
                return self.domain
        if self.peer is not None and self.peer.domain is not None:
            if instantiates(self.peer.domain, type):
                return self.peer
        return None
        
    
#############################################################################
#############################################################################

class Marking(trellis.Component):
    """Assignment of some tokens to a component."""

    def __add__(self, other):
        return self
    
    def __radd__(self, other):
        if other:
            return other
        return self
    
    def __sub__(self, other):
        if other:
            return None
        else:
            return self

    def __rsub__(self, other):
        raise ValueError(other)
        
    def __nonzero__(self):
        return True

#############################################################################
#############################################################################

class Flow(collections.Iterable):
    """A marking associated with an arc."""
    
    def __init__(self, arc=None, marking=None,):
        self.marking = marking
        self.arc = arc # TODO: make this immutable so it doesn't break hash()
    
    path = property(lambda self: () if self.arc is None else (self.source,\
                                                              self.input,\
                                                              self.arc.input,\
                                                              self.arc,\
                                                              self.arc.output,\
                                                              self.output,\
                                                              self.sink))
    source = property(lambda self: None if self.arc is None else self.arc.source)
    sink = property(lambda self: None if self.arc is None else self.arc.sink)
    input = property(lambda self: None if self.arc is None else self.arc.input.input)
    output = property(lambda self: None if self.arc is None else self.arc.output.output)

    def __hash__(self):
        return hash(self.arc)

    def __cmp__(self):
        return cmp(self.arc)

    def __iter__(self):
        for hop in self.path:
            yield hop

    def intersects(self, other):
        path = other.path
        for p in self.path:
            if p in path:
                return p
        return None

    
#############################################################################
#############################################################################

class Event(collections.MutableSet, collections.Callable):
    """Collection of flows."""
    
    Marking = Marking
    
    def __init__(self, transition=None, flows=None):
        self.transition = transition
        self.flows = set() if flows is None else flows
    
    def __len__(self):
        return len(self.flows)
    
    def __contains__(self, item):
        return item in self.flows
    
    def __iter__(self):
        for item in self.flows:
            yield item
    
    def add(self, item):
        self.flows.add(item)
    
    def discard(self, item):
        self.flows.discard(item)
    
    @trellis.modifier
    def __call__(self):
        transition = self.transition
        input = (transition >> self)
        output = transition(input)
        output = (transition << output)
        return output

#############################################################################
#############################################################################

class Arc(Relation, pypetri.hierarchy.Composer):
    
    NAME_INPUT = str(Relation.INPUT)
    NAME_OUTPUT = str(Relation.OUTPUT)
    
    Port = Port
    Flow = Flow

    def __init__(self, *types, **kwargs):
        Relation.__init__(self, *types)
        pypetri.hierarchy.Composer.__init__(self, **kwargs)
        input = self.Port(self.types[self.INPUT], self.__class__, name=self.NAME_INPUT)
        output = self.Port(self.__class__, self.types[self.OUTPUT], name=self.NAME_OUTPUT)
        self.add(input)
        self.add(output)
    
    @trellis.maintain
    def input(self):
        name = self.NAME_INPUT
        if name in self:
            return self[name]
        else:
            return None
    
    @trellis.maintain
    def output(self):
        name = self.NAME_OUTPUT
        if name in self:
            return self[name]
        else:
            return None
    
    @trellis.maintain
    def source(self):
        input = self.input
        if input is not None and input.input is not None:
            return input.input.domain
        return None    

    @trellis.maintain
    def sink(self):
        output = self.output
        if output is not None and output.output is not None:
            return output.output.domain
        return None
    
    def __rshift__(self, other):
        return self.input >> other
    
    def __lshift__(self, other):
        return self.output << other
                
    def search(self):
        """Returns an iterator over a set of enabling Flows."""
        if self.source is None:
            return
        enabled = self.enabled
        marking = self.source.marking
        if marking:
            flow = self.Flow(arc=self, marking=marking,)
            if enabled(flow):
                yield flow
    
    def enabled(self, flow):
        return True

#############################################################################
#############################################################################

class Vertex(pypetri.hierarchy.Composer):
    """Petri net vertex has a set of input arcs and a set of output arcs."""
    
    Port = Port
    
    @trellis.maintain
    def inputs(self): # FIXME: DRY
        if self.contains is None or len(self.contains) == 0:
            return set()
        current = self.inputs
        changes = self.contains
        filter = lambda x: instantiates(self, x.types[x.OUTPUT])
        result = update(current, changes, filter)
        return result
    
    @trellis.maintain
    def outputs(self): # FIXME: DRY
        if self.contains is None or len(self.contains) == 0:
            return set()
        current = self.outputs
        changes = self.contains
        filter = lambda x: instantiates(self, x.types[x.INPUT])
        result = update(current, changes, filter)
        return result
        
#############################################################################
#############################################################################

class Condition(Vertex):
    
    Marking = Marking
    
    marking = trellis.attr(None)
        
    @trellis.modifier
    def __rshift__(self, other):
        self.marking -= other.marking
        return other
    
    @trellis.modifier
    def __lshift__(self, other):
        self.marking += other.marking
        return other
        
#############################################################################
#############################################################################

class Transition(collections.Callable, Vertex):
    
    Event = Event
    Flow = Flow
    
    def search(self, searcher=None):
        """Returns an iterator over a set of enabling Events.
        
        There exists some (possibly empty) set of input arc flow
        combinations that satisfy this transition.  This set of possible
        inputs is distinct from the heuristic used to sample this set.
        """
        # A brute-force, general approach is to yield all combinations
        # (n choose k for k in 1..n) of enabling events from all inputs.
        # We don't care about ordering (why we don't do permutations),
        # and there is no repetition.
        searcher = brute if searcher is None else searcher
        enabled = self.enabled
        
        def next(input):
            arc = input.input.input
            for f in arc.search():
                yield f
                
        def inputs():
            for i in self.inputs:
                if i.connected and i.input.input is not None:
                    yield next(i)
            
        for flows in searcher(inputs()):
            event = self.Event(transition=self, flows=flows)
            if len(flows) > 0 and enabled(event):
                yield event
                    
    def enabled(self, event):
        incoming = [i.input.input for i in self.inputs if i.connected]
        return len(event) == len(incoming)
    
    def __call__(self, event):
        """Returns a set of outputs."""
        outputs = self.Event(transition=self,)
        outgoing = [o.output.output for o in self.outputs if o.connected]
        for arc in outgoing:
            output = self.Flow(arc=arc, marking=outputs.Marking())
            outputs.add(output)
        return outputs
    
    @trellis.modifier
    def __rshift__(self, flows):
        outputs = self.Event(transition=self,)
        for flow in flows:
            output = flow.output >> flow
            outputs.add(output)
        return outputs
    
    @trellis.modifier    
    def __lshift__(self, flows):
        outputs = self.Event(transition=self,)
        for flow in flows:
            output = flow.input << flow
            outputs.add(output)
        return outputs

#############################################################################
#############################################################################

class Network(collections.Callable, pypetri.hierarchy.Composer):
    """Fires one transition at a time.
    
    I considered two options for executing events. One was to
    find and execute a set of non-conflicting events concurrently.
    However, without domain knowledge, determining whether events
    are conflicting or not seems tricky, as one must consider both
    the input and output conditions.
    
    The simpler option is to only execute one event at a time.
    This essentially enforces serialization on events, but seems
    simpler to reason about and to implement.
    """
    
    ARC_TOKEN = '->'
    
    Arc = Arc
    Condition = Condition
    Transition = Transition
    Port = Port

    @trellis.modifier
    def __call__(self, event):
        return event()

    def zip(self, odd, even, **kwargs):
        if 0 in [len(x) for x in (odd, even,)]:
            return
        iters = iter(odd), iter(even)
        pair = iters[0].next(), iters[1].next()
        while True:
            pair = [self[x] if isinstance(x, str) else x for x in pair]
            self.connect(*pair, **kwargs)
            try:
                pair = pair[1], iters[0].next()
                iters = iters[1], iters[0]
            except StopIteration:
                break
    
    @trellis.maintain
    def arcs(self): # FIXME: DRY
        if self.contains is None or len(self.contains) == 0:
            return set()
        current = self.arcs
        changes = self.contains
        filter = lambda x: instantiates(x, self.Arc)
        result = update(current, changes, filter)
        return result

    @trellis.maintain
    def conditions(self): # FIXME: DRY
        if self.contains is None or len(self.contains) == 0:
            return set()
        current = self.conditions
        changes = self.contains
        filter = lambda x: instantiates(x, self.Condition)
        result = update(current, changes, filter)
        return result
        
    @trellis.maintain
    def transitions(self): # FIXME: DRY
        if self.contains is None or len(self.contains) == 0:
            return set()
        current = self.transitions
        changes = self.contains
        filter = lambda x: instantiates(x, self.Transition)
        result = update(current, changes, filter)
        return result
    
    @trellis.maintain
    def networks(self): # FIXME: DRY
        if None in (self.arcs, self.transitions, self.conditions,):
            return set()
        # assume that subcomponents that are unclassified are networks
        all = set(self.contains.itervalues())
        leftover = all - (self.arcs | self.transitions | self.conditions)
        return leftover
    
    def search(self, components=None):
        if components is None:
            components = self.transitions | self.networks
        for sub in components:
            for event in sub.search():
                yield event

    def connect(self, source, sink, arc=None, **kwargs):
        output = None
        input = None
        if isinstance(source, self.Port):
            output = source
            source = output.input
        if isinstance(sink, self.Port):
            input = sink
            sink = input.output
        if arc is None:
            names = (source.uid, sink.uid,)
            name = self.ARC_TOKEN.join(names)
            types = []
            for cls in source.__class__, sink.__class__:
                for t in self.Condition, self.Transition:
                    if issubclass(cls, t):
                        types.append(t)
                        break
            arc = self.Arc(*types, name=name, **kwargs)
            self.add(arc)
        if output is None:
            output = self.open(source, arc.name, input=False)
        if input is None:
            input = self.open(sink, arc.name, input=True)
        arc.input.connect(output)
        arc.output.connect(input)
        return arc

    def open(self, vertex, port, input=True):
        if isinstance(vertex, str):
            vertex = self[vertex]
        if input:
            types = self.Arc, vertex.__class__,
        else:
            types = vertex.__class__, self.Arc,
        p = vertex.Port(types[0], types[1], name=port,)
        vertex.add(p)
        return p
    
# was written to discover whether concurrent events conflict
# unused for now
#    def enabled(self, events):
#        # map flows to shared vertices
#        shared = {}
#        for e in events:
#            for f in e.flows:
#                start = f.source.uid
#                if start not in shared:
#                    shared[start] = set()
#                shared[start].add(f)
#        for uid, flows in shared.iteritems():
#            start = self.top.find(uid)
#            if not start.enabled(flows):
#                return False
#        return True

#############################################################################
#############################################################################
