# @copyright
# @license

import examples.simple as simple


#
# Net for a single light
#

class Light(simple.TokenNetwork):
    
    CONDITIONS = ["RED", "GREEN", "YELLOW",]
    TRANSITIONS = ["RED2GREEN", "GREEN2YELLOW", "YELLOW2RED",]

    @classmethod
    def create(cls, *args, **kwargs):
        self = cls(*args, **kwargs)
        # arcs create a circular network
        self.zip(self.CONDITIONS, self.TRANSITIONS)
        self.zip(self.TRANSITIONS[-1:], self.CONDITIONS[0:1])
        start = self[self.CONDITIONS[0]]
        start.marking.count = 1
        return self

    def __init__(self, *args, **kwargs):
        super(Light, self).__init__(*args, **kwargs)
        # light states and transitions
        for cls, names in ((self.Condition, self.CONDITIONS), 
                           (self.Transition, self.TRANSITIONS)):
            vertices = [cls(name=x) for x in names]
            for x in vertices:
                self.add(x)

    def connect(self, source, sink, **kwargs):
        start = self[self.CONDITIONS[0]]
        if start in (source, sink):
            demand = 1
        else:
            demand = 2
        return super(Light, self).connect(source, sink, demand=demand, **kwargs)
        
#
# Net composed of two light subnets
#

class FourWayIntersection(simple.TokenNetwork):

    # Global start state
    START = 'START'

    # Light names
    LIGHTS = ['A', 'B']


    @classmethod
    def create(cls, *args, **kwargs):
        self = cls(*args, **kwargs)
        start = self[self.START]
        for l in self.LIGHTS:
            light = Light.create(name=l)
            self.add(light)
        for l in self.LIGHTS:
            light = self[l]
            # input to light
            self.connect(start, light[light.TRANSITIONS[0]])
            # output from light
            self.connect(light[light.TRANSITIONS[-1]], start)
        return self
    
    def __init__(self, *args, **kwargs):
        super(FourWayIntersection, self).__init__(*args, **kwargs)
        start = self.Condition(name=self.START)
        self.add(start)
        start.marking.count = 1
                
create = FourWayIntersection.create
