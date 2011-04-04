# @copyright
# @license

import examples.simple as simple


#
# Net for a single light
#

class Light(simple.SimpleNetwork):
    
    CONDITIONS = ["green", "yellow", "red",]
    TRANSITIONS = ["red2green", "green2yellow", "yellow2red",]
    ARCS = [(TRANSITIONS[0], CONDITIONS[0]),
            (CONDITIONS[0], TRANSITIONS[1]),
            (TRANSITIONS[1], CONDITIONS[1]),
            (CONDITIONS[1], TRANSITIONS[2]),
            (TRANSITIONS[2], CONDITIONS[2]),
            (CONDITIONS[2], TRANSITIONS[0]),]

    @classmethod
    def create(cls, *args, **kwargs):
        light = cls(*args, **kwargs)
        
        # light states
        conditions = [light.Condition(name=n) for n in light.CONDITIONS]
        for hub in conditions:
            light.add(hub)
        
        # light transitions
        transitions = [light.Transition(name=n) for n in light.TRANSITIONS]
        for hub in transitions:
            light.add(hub)
        
        # arcs
        for pair in light.ARCS:
            capacity = 1 if "red" in pair else 2
            hubs = [light.find(n) for n in pair]
            light.connect(hubs[0], hubs[1], capacity)
        
        return light


#
# Net composed of two light subnets
#

class TwoWayIntersection(simple.SimpleNetwork):

    # Global start state
    START = 'start'

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
            intersect.connect(start, light.find(Light.TRANSITIONS[0]))
            
            # output from light
            intersect.connect(light.find(Light.TRANSITIONS[-1]), start)
    
        # Initial markings
        start.marking.count = 1
        for l in intersect.LIGHTS:
            light = intersect.find(l)
            red = light.find(Light.CONDITIONS[-1])
            red.marking.count = 1
        
        return intersect

create = TwoWayIntersection.create
