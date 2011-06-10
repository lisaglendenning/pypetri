# @copyright
# @license

import types
import functools

from pypetri import trellis
from pypetri import net
from pypetri.collections import flow, sets

#############################################################################
#############################################################################

#
# Flow Network such that the flow must equal the maximum
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

#############################################################################
#############################################################################

#
# Net for a single light
#

class Light(ExactFlow):
    
    CONDITIONS = ["RED", "GREEN", "YELLOW",]
    TRANSITIONS = ["RED2GREEN", "GREEN2YELLOW", "YELLOW2RED",]
    
    def Condition(self, name, **kwargs):
        capacity = 1 if name == self.CONDITIONS[0] else 2
        marking = 1 if name == self.CONDITIONS[0] else 0
        return super(Light, self).Condition(maximum=capacity, marking=marking, **kwargs)

    def Output(self, name, **kwargs):
        CONDITIONS = self.CONDITIONS
        TRANSITIONS = self.TRANSITIONS
        if name in CONDITIONS:
            i = CONDITIONS.index(name)
            j = i
            next = TRANSITIONS[j]
        else:
            i = TRANSITIONS.index(name)
            j = 0 if (i == len(TRANSITIONS)-1) else i+1
            next = CONDITIONS[j]
        source = getattr(self, name.lower())
        sink = getattr(self, next.lower())
        for o in source.outputs:
            if o.output is sink:
                break
        else:
            self.Arc(source, sink, **kwargs)
        return source

    red = trellis.maintain(rule=lambda self: self.Output('RED'), 
                           make=lambda self: self.Condition('RED'))
    green = trellis.maintain(rule=lambda self: self.Output('GREEN'), 
                             make=lambda self: self.Condition('GREEN'))
    yellow = trellis.maintain(rule=lambda self: self.Output('YELLOW'), 
                              make=lambda self: self.Condition('YELLOW'))

    red2green = trellis.maintain(rule=lambda self: self.Output('RED2GREEN'), 
                                 make=lambda self: self.Transition())
    green2yellow = trellis.maintain(rule=lambda self: self.Output('GREEN2YELLOW'), 
                                    make=lambda self: self.Transition())
    yellow2red = trellis.maintain(rule=lambda self: self.Output('YELLOW2RED'), 
                                  make=lambda self: self.Transition())
    
#############################################################################
#############################################################################

#
# Net composed of two light subnets
#

class Intersection(ExactFlow):

    # Global start state
    CONDITIONS = ['START',]

    lights = trellis.make(sets.Set)
    
    @trellis.maintain(make=lambda self: self.Condition(maximum=1, marking=1))
    def start(self):
        condition = self.start
        for light in self.lights:
            input = getattr(light, light.TRANSITIONS[-1].lower())
            output = getattr(light, light.TRANSITIONS[0].lower())
            for o in condition.outputs:
                if o.output is output:
                    break
            else:
                self.Arc(condition, output)
            for i in condition.inputs:
                if i.input is input:
                    break
            else:
                self.Arc(input, condition)
        return condition

    def __init__(self, ways=2, *args, **kwargs):
        attr = 'lights'
        if attr not in kwargs:
            kwargs[attr] = sets.Set([Light() for i in xrange(ways)])
        super(Intersection, self).__init__(*args, **kwargs)

#############################################################################
#############################################################################

Network = Intersection

#############################################################################
#############################################################################
