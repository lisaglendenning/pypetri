
import examples.simple as simple

#
# Net for a single light
#

CONDITIONS = ["green", "yellow", "red",]
TRANSITIONS = ["red2green", "green2yellow", "yellow2red",]
ARCS = [(TRANSITIONS[0], CONDITIONS[0]),
        (CONDITIONS[0], TRANSITIONS[1]),
        (TRANSITIONS[1], CONDITIONS[1]),
        (CONDITIONS[1], TRANSITIONS[2]),
        (TRANSITIONS[2], CONDITIONS[2]),
        (CONDITIONS[2], TRANSITIONS[0]),]
    
def create_light(name=''):
    pnet = simple.SimpleNetwork(name=name)
    
    # light states
    conditions = [pnet.Condition(name=n) for n in CONDITIONS]
    for hub in conditions:
        pnet.add(hub)
    
    # light transitions
    transitions = [pnet.Transition(name=n) for n in TRANSITIONS]
    for hub in transitions:
        pnet.add(hub)
    
    # arcs
    for pair in ARCS:
        capacity = 1 if "red" in pair else 2
        hubs = [pnet.find(n) for n in pair]
        pnet.connect(hubs[0], hubs[1], capacity)
    
    return pnet

#
# Net composed of two light subnets
#

LIGHTS = ['A', 'B']

# Global start state
START = 'start'

def create(name=''):
    pnet = simple.SimpleNetwork(name=name)
    
    start = pnet.Condition(name=START)
    pnet.add(start)
    
    for light in LIGHTS:
        lightnet = create_light(light)
        pnet.add(lightnet)
        
        # input to light
        pnet.connect(start, lightnet.find(TRANSITIONS[0]))
        
        # output from light
        pnet.connect(lightnet.find(TRANSITIONS[-1]), start)

    # Initial markings
    start.marking.count = 1
    for light in LIGHTS:
        lightnet = pnet.find(light)
        red = lightnet.find(CONDITIONS[-1])
        red.marking.count = 1
    
    return pnet
