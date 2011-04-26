# @copyright
# @license

import types

from pypetri.collections import flow

#############################################################################
#############################################################################

#
# Net for a single light
#

class Light(flow.Network):
    
    CONDITIONS = ["RED", "GREEN", "YELLOW",]
    TRANSITIONS = ["RED2GREEN", "GREEN2YELLOW", "YELLOW2RED",]

    def __new__(cls, *args, **kwargs):
        self = super(Light, cls).__new__(cls, *args, **kwargs)
        self.conditions = []
        for name in self.CONDITIONS:
            capacity = 1 if name == self.CONDITIONS[0] else 2
            condition = self.Condition(minimum=0, maximum=capacity)
            self.conditions.append(condition)
        self.transitions = []
        for name in self.TRANSITIONS:
            transition = self.Transition()
            transition.predicate = types.MethodType(lambda self, flow: flow == self.maximum, transition, transition.__class__)
            self.transitions.append(transition)
        for vertices in self.conditions, self.transitions:
            self.vertices.update(vertices)
        
        # arcs create a circular network
        arcs = []
        for i in xrange(len(self.conditions)):
            j = i+1 if i < len(self.conditions)-1 else 0
            for arc in self.link((self.conditions[i], self.transitions[i], self.conditions[j],)):
                arcs.append(arc)
        
        # and, initial marking
        self.conditions[0].marking = 1
        return self

#############################################################################
#############################################################################

#
# Net composed of two light subnets
#

class FourWayIntersection(flow.Network):

    # Global start state
    CONDITIONS = ['START',]

    # Light names
    LIGHTS = ['A', 'B',]

    def __new__(cls, *args, **kwargs):
        self = super(FourWayIntersection, cls).__new__(cls, *args, **kwargs)
        
        self.conditions = []
        for name in self.CONDITIONS:
            capacity = 1
            condition = self.Condition(minimum=0, maximum=capacity)
            self.conditions.append(condition)
            
        self.lights = []
        for name in self.LIGHTS:
            light = Light()
            self.lights.append(light)
        for vertices in self.conditions, self.lights:
            self.vertices.update(vertices)
        
        start = self.conditions[0]
        arcs = []
        for light in self.lights:
            # input and output to light
            pairs = ((start, light.transitions[0]),
                     (light.transitions[-1], start,),)
            for pair in pairs:
                for arc in self.link(pair):
                    arcs.append(arc)

        # and, initial marking
        self.conditions[0].marking = 1

        return self

#############################################################################
#############################################################################

Network = FourWayIntersection

#############################################################################
#############################################################################
