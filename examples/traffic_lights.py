# @copyright
# @license

import types
import functools

from pypetri import trellis
from pypetri.collections import flow

#############################################################################
#############################################################################

#
# Net for a single light
#

class Light(flow.Network):
    
    CONDITIONS = ["RED", "GREEN", "YELLOW",]
    TRANSITIONS = ["RED2GREEN", "GREEN2YELLOW", "YELLOW2RED",]

    red = trellis.make(None)
    green = trellis.make(None)
    yellow = trellis.make(None)
    red2green = trellis.make(None)
    green2yellow = trellis.make(None)
    yellow2red = trellis.make(None)

    def __init__(self, *args, **kwargs):
        names = self.CONDITIONS
        for v in names:
            if v.lower() not in kwargs:
                capacity = 1 if v == names[0] else 2
                marking = 1 if v == names[0] else 0
                condition = self.Condition(minimum=0, maximum=capacity, marking=marking,)
                kwargs[v.lower()] = condition
        names = self.TRANSITIONS
        for v in names:
            if v.lower() not in kwargs:
                transition = self.Transition()
                mux = transition.mux
                predicate = types.MethodType(lambda self, flow: flow == self.maximum, mux, mux.__class__)
                transition.mux.predicate = predicate
                kwargs[v.lower()] = transition
        super(Light, self).__init__(*args, **kwargs)
        conditions = []
        transitions = []
        for ls, names in ((conditions, self.CONDITIONS), (transitions, self.TRANSITIONS,),):
            for name in names:
                v = getattr(self, name.lower())
                ls.append(v)
                self.vertices.add(v)

        # arcs create a circular network
        for i in xrange(len(conditions)):
            j = i+1 if i < len(conditions)-1 else 0
            chain = (conditions[i], transitions[i], conditions[j],)
            for arc in self.chain(chain):
                pass


#############################################################################
#############################################################################

#
# Net composed of two light subnets
#

class Intersection(flow.Network):

    # Global start state
    CONDITIONS = ['START',]

    start = trellis.attr(None)
    lights = trellis.make(trellis.Set)

    def __init__(self, ways=2, *args, **kwargs):
        for name in self.CONDITIONS:
            if name.lower() not in kwargs:
                capacity = 1
                marking = 1
                condition = self.Condition(minimum=0, maximum=capacity, marking=marking)
                kwargs[name.lower()] = condition
        if 'lights' not in kwargs:
            kwargs['lights'] = trellis.Set([Light() for i in xrange(ways)])
        super(Intersection, self).__init__(*args, **kwargs)
        self.vertices.add(self.start)
        for light in self.lights:
            self.vertices.add(light)
        for light in self.lights:
            input = getattr(light, light.TRANSITIONS[-1].lower())
            output = getattr(light, light.TRANSITIONS[0].lower())
            chain = (input, self.start, output,)
            for arc in self.chain(chain):
                pass
        
#############################################################################
#############################################################################

Network = Intersection

#############################################################################
#############################################################################
