# @copyright
# @license

import itertools

from pypetri import trellis
from pypetri.collections import flow

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
            kwargs['minimum'] = 0
        return super(ExactFlow, self).Condition(*args, **kwargs)
    
    def Transition(self, *args, **kwargs):
        if 'demux' not in kwargs:
            kwargs['demux'] = flow.Transition.Demultiplexer(predicate=self.ismax)
        return super(ExactFlow, self).Transition(*args, **kwargs)

    def toname(self, obj):
        if obj is self:
            return self.__class__.__name__
        
#############################################################################
#############################################################################

#
# Net for a single light
#

class Light(ExactFlow):
    
    CONDITIONS = ["RED", "GREEN", "YELLOW",]
    TRANSITIONS = ["RED2GREEN", "GREEN2YELLOW", "YELLOW2RED",]
    
    @trellis.modifier
    def Arcs(self):
        CONDITIONS = self.CONDITIONS
        TRANSITIONS = self.TRANSITIONS
        inputs = itertools.izip(CONDITIONS, TRANSITIONS)
        outputs = itertools.izip(TRANSITIONS, itertools.chain(itertools.islice(CONDITIONS, 1, len(CONDITIONS)),
                                                              itertools.islice(CONDITIONS, 1)))
        pairs = itertools.chain(inputs, outputs)
        for pair in pairs:
            pair = tuple([getattr(self, name.lower()) for name in pair])
            self.Arc(*pair)

    def Condition(self, name, **kwargs):
        capacity = 1 if name == self.CONDITIONS[0] else 2
        marking = 1 if name == self.CONDITIONS[0] else 0
        return super(Light, self).Condition(maximum=capacity, marking=marking, **kwargs)

    def __init__(self, *args, **kwargs):
        super(Light, self).__init__(*args, **kwargs)
        self.Arcs()

    # TODO: trying to figure out how to automate the following declarations...
    red = trellis.make(lambda self: self.Condition('RED'))
    green = trellis.make(lambda self: self.Condition('GREEN'))
    yellow = trellis.make(lambda self: self.Condition('YELLOW'))

    red2green = trellis.make(lambda self: self.Transition())
    green2yellow = trellis.make(lambda self: self.Transition())
    yellow2red = trellis.make(lambda self: self.Transition())
    
    def toname(self, obj):
        for name in itertools.chain(self.CONDITIONS, self.TRANSITIONS):
            if obj is getattr(self, name.lower()):
                return name
        return super(Light, self).toname(obj)

#############################################################################
#############################################################################

#
# Net composed of two light subnets
#

class Intersection(ExactFlow):

    # Global start state
    CONDITIONS = ['START',]

    lights = trellis.make(tuple)
    start = trellis.make(lambda self: self.Condition(maximum=1, marking=1))
    
    @trellis.modifier
    def Arcs(self):
        condition = self.start
        for light in self.lights:
            input = getattr(light, light.TRANSITIONS[-1].lower())
            output = getattr(light, light.TRANSITIONS[0].lower())
            for pair in ((input, condition), (condition, output),):
                self.Arc(*pair)

    def __init__(self, ways=2, *args, **kwargs):
        attr = 'lights'
        if attr not in kwargs:
            kwargs[attr] = tuple([x() for x in itertools.repeat(Light, ways)])
        super(Intersection, self).__init__(*args, **kwargs)
        self.Arcs()

    def toname(self, obj):
        for name in self.CONDITIONS:
            if obj is getattr(self, name.lower()):
                return name
        if obj in self.lights:
            return str(self.lights.index(obj))
        return super(Intersection, self).toname(obj)
    
#############################################################################
#############################################################################

Network = Intersection

#############################################################################
#############################################################################
