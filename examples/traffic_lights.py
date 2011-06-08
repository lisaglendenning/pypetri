# @copyright
# @license

import types
import functools

from pypetri import trellis
from pypetri import net
from pypetri.collections import flow

#############################################################################
#############################################################################

#
# Flow must equal maximum
#

class ExactFlow(flow.Network):
    
    @classmethod
    def ismax(cls, flow, min, max):
        return flow == max

    def Condition(self, *args, **kwargs):
        if 'minimum' not in kwargs:
            minimum = 0
        return super(ExactFlow, self).Condition(*args, **kwargs)
    
    def Transition(self, *args, **kwargs):
        if 'demux' not in kwargs:
            kwargs['demux'] = flow.Transition.Demultiplexer(predicate=self.ismax)
        return super(ExactFlow, self).Transition(*args, **kwargs)

#
# Net for a single light
#

class Light(ExactFlow):
    
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
            attr = v.lower()
            if attr not in kwargs:
                capacity = 1 if v == names[0] else 2
                marking = 1 if v == names[0] else 0
                condition = self.Condition(maximum=capacity, marking=marking,)
                kwargs[attr] = condition
        names = self.TRANSITIONS
        for v in names:
            attr = v.lower()
            if attr not in kwargs:
                transition = self.Transition()
                kwargs[attr] = transition
        super(Light, self).__init__(*args, **kwargs)
        conditions = []
        transitions = []
        for ls, names in ((conditions, self.CONDITIONS), (transitions, self.TRANSITIONS,),):
            for name in names:
                v = getattr(self, name.lower())
                ls.append(v)

        # arcs create a circular network
        for i in xrange(len(conditions)):
            j = i+1 if i < len(conditions)-1 else 0
            for pair in ((conditions[i], transitions[i],),
                         (transitions[i], conditions[j],),):
                arc = self.Arc(*pair)


#############################################################################
#############################################################################

#
# Net composed of two light subnets
#

class Intersection(ExactFlow):

    # Global start state
    CONDITIONS = ['START',]

    start = trellis.make(None)
    lights = trellis.make(trellis.Set)

    def __init__(self, ways=2, *args, **kwargs):
        for name in self.CONDITIONS:
            attr = name.lower()
            if attr not in kwargs:
                capacity = 1
                marking = 1
                condition = self.Condition(maximum=capacity, marking=marking)
                kwargs[attr] = condition
        attr = 'lights'
        if attr not in kwargs:
            kwargs[attr] = trellis.Set([Light() for i in xrange(ways)])
        super(Intersection, self).__init__(*args, **kwargs)

        #
        # arcs
        #

        start = self.start
        for light in self.lights:
            input = getattr(light, light.TRANSITIONS[-1].lower())
            output = getattr(light, light.TRANSITIONS[0].lower())
            for pair in ((input, start), (start, output)):
                arc = self.Arc(*pair)

#############################################################################
#############################################################################

Network = Intersection

#############################################################################
#############################################################################
