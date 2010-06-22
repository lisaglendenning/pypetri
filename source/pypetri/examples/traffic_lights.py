
import pypetri.hub as phub
import pypetri.models.classic.model as pclassic

def create(name=''):
    pnet = pclassic.ClassicCollective(name=name)
    start = pnet.declarations.Condition(name="start")
    pnet.add(start)
    for light in ["A", "B"]:
        names = ["%s%s" % (light, n) for n in ["green", "yellow", "red"]]
        conditions = [pnet.declarations.Condition(name=n) for n in names]
        for hub in conditions:
            pnet.add(hub)
        names = ["%s%s" % (light, n) for n in ["green2yellow", "yellow2red", "red2green"]]
        transitions = [pnet.declarations.Transition(name=n) for n in names]
        for hub in transitions:
            pnet.add(hub)
        for pair in [("green", "green2yellow"),("green2yellow", "yellow"),
                     ("yellow", "yellow2red"),("yellow2red", "red"),
                     ("red", "red2green"),("red2green", "green"),]:
            capacity = 1 if "red" in pair else 2
            pair = ["%s%s" % (light, n) for n in pair]
            hubs = [pnet.find(n) for n in pair]
            pnet.connect(hubs, capacity)
        
        hubs = [pnet.find("%syellow2red" % light), start]
        pnet.connect(hubs)
        hubs = [start, pnet.find("%sred2green" % light)]
        pnet.connect(hubs)
    return pnet
