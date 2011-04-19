# @copyright
# @license

import examples.simple as simple


#
# Net for a single light
#

class Light(simple.SimpleNetwork):
    
    CONDITIONS = ["RED", "GREEN", "YELLOW",]
    TRANSITIONS = ["RED2GREEN", "GREEN2YELLOW", "YELLOW2RED",]

    @classmethod
    def create(cls, *args, **kwargs):
        light = cls(*args, **kwargs)
        
        conditions = light.CONDITIONS
        transitions = light.TRANSITIONS
        
        # light states and transitions
        for cls, names in ((light.Condition, conditions), 
                           (light.Transition, transitions)):
            vertices = [cls(name=x) for x in names]
            for x in vertices:
                light.add(x)
        
        # arcs create a circular network
        start = light[conditions[0]]
        for i in xrange(len(conditions)):
            if i == len(conditions) - 1:
                j = 0
            else:
                j = i + 1
            conds = [light[conditions[x]] for x in i,j]
            tran = light[transitions[i]]
            for pair in ((conds[0], tran,),(tran, conds[1]),):
                demand = 1 if start in pair else 2
                arc = light.connect(pair[0], pair[1], demand)
        
        return light

    def initialize(self):
        start = self[self.CONDITIONS[0]]
        start.marking.count = 1

#
# Net composed of two light subnets
#

class TwoWayIntersection(simple.SimpleNetwork):

    # Global start state
    START = 'START'

    # Light names
    LIGHTS = ['A', 'B']


    @classmethod
    def create(cls, *args, **kwargs):
        intersect = cls(*args, **kwargs)
        
        start = intersect.Condition(name=intersect.START)
        intersect.add(start)
        
        for l in intersect.LIGHTS:
            light = Light.create(name=l)
            intersect.add(light)
            
            # input to light
            intersect.connect(start, light[light.TRANSITIONS[0]])
            
            # output from light
            intersect.connect(light[light.TRANSITIONS[-1]], start)
    
        intersect.initialize()
        return intersect
    
    def initialize(self):

        # Initial markings
        # Each light begins in the red state
        start = self[self.START]
        start.marking.count = 1
        for l in self.LIGHTS:
            light = self[l]
            light.initialize()
            
create = TwoWayIntersection.create
