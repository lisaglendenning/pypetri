# @copyright
# @license

import types

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
    
    red = trellis.attr(None)
    green = trellis.attr(None)
    yellow = trellis.attr(None)
    red2green = trellis.attr(None)
    green2yellow = trellis.attr(None)
    yellow2red = trellis.attr(None)

    def __init__(self, *args, **kwargs):
        for name in self.CONDITIONS:
            if name.lower() not in kwargs:
                capacity = 1 if name == self.CONDITIONS[0] else 2
                marking = 1 if name == self.CONDITIONS[0] else 0
                condition = self.Condition(minimum=0, maximum=capacity, marking=marking)
                kwargs[name.lower()] = condition
        for name in self.TRANSITIONS:
            if name.lower() not in kwargs:
                transition = self.Transition()
                transition.predicate = types.MethodType(lambda self, flow: flow == self.maximum, transition, transition.__class__)
                kwargs[name.lower()] = transition
        super(Light, self).__init__(*args, **kwargs)
    
    @trellis.maintain
    def links(self):
        conditions = [getattr(self, name.lower()) for name in self.CONDITIONS]
        transitions = [getattr(self, name.lower()) for name in self.TRANSITIONS]
        for vertices in (conditions, transitions,):
            for v in vertices:
                if v not in self.vertices:
                    self.vertices.add(v)
                    
        # arcs create a circular network
        for i in xrange(len(conditions)):
            j = i+1 if i < len(conditions)-1 else 0
            chain = (conditions[i], transitions[i], conditions[j],)
            for i in chain[1].inputs:
                if i.input is chain[0]:
                    break
            else:
                for i in chain[1].inputs:
                    if i.input is None:
                        chain[0].outputs.add(i)
                        break
                else:
                    self.link(chain[0], chain[1])
            for o in chain[1].outputs:
                if o.output is chain[2]:
                    break
            else:
                for o in chain[1].outputs:
                    if o.output is None:
                        chain[2].inputs.add(o)
                        break
                else:
                    self.link(chain[1], chain[2])


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
        

    @trellis.maintain
    def links(self):
        conditions = self.start, 
        for vertices in (conditions, self.lights,):
            for v in vertices:
                if v not in self.vertices:
                    self.vertices.add(v)

        start = self.start
        for light in self.lights:
            # input and output to light
            output = getattr(light, light.TRANSITIONS[0].lower())
            input = getattr(light, light.TRANSITIONS[-1].lower())
            for i in start.inputs:
                if i.input is input:
                    break
            else:
                for i in start.inputs:
                    if i.input is None:
                        inputs.outputs.add(i)
                        break
                else:
                    self.link(input, start)
            for o in start.outputs:
                if o.output is output:
                    break
            else:
                for o in start.outputs:
                    if o.output is None:
                        output.inputs.add(o)
                        break
                else:
                    self.link(start, output)
        
#############################################################################
#############################################################################

Network = Intersection

#############################################################################
#############################################################################
