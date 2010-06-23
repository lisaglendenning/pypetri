
import pypetri.models.classic.model as pclassic

def create_light(name=''):
    pnet = pclassic.ClassicCollective(name=name)
    names = ["green", "yellow", "red"]
    conditions = [pnet.declarations.Condition(name=n) for n in names]
    for hub in conditions:
        pnet.add(hub)
    names = ["green2yellow", "yellow2red", "red2green"]
    transitions = [pnet.declarations.Transition(name=n) for n in names]
    for hub in transitions:
        pnet.add(hub)
    for pair in [("green", "green2yellow"),("green2yellow", "yellow"),
                 ("yellow", "yellow2red"),("yellow2red", "red"),
                 ("red", "red2green"),("red2green", "green"),]:
        capacity = 1 if "red" in pair else 2
        hubs = [pnet.find(n) for n in pair]
        pnet.create_arc(hubs, capacity)
    
    # input and output connectors
    domains = [pnet.declarations.Arc, pnet.declarations.Transition]
    inc = pnet.declarations.Relation(domains=domains, name='in')
    int = pnet.find('red2green')
    int.add(inc)
    outc = pnet.declarations.Relation(domains=domains[::-1], name='out')
    outt = pnet.find('yellow2red')
    outt.add(outc)
    return pnet

def create(name=''):
    pnet = pclassic.ClassicCollective(name=name)
    start = pnet.declarations.Condition(name="start")
    pnet.add(start)
    lights = ['A', 'B']
    for light in lights:
        lightnet = create_light(light)
        
        lightc = { }
        for p in lightnet.peerings:
            if p.find('in') >= 0:
                lightc['in'] = lightnet.get(p)
            elif p.find('out') >= 0:
                lightc['out'] = lightnet.get(p)
        
        pnet.add(lightnet)
        
        # input and output connectors
        domains = [pnet.declarations.Condition, pnet.declarations.Arc]
        outc = pnet.declarations.Relation(domains=domains, name='out%s' % light)
        start.add(outc)
        inc = pnet.declarations.Relation(domains=domains[::-1], name='in%s' % light)
        start.add(inc)
        domains = [pnet.declarations.Condition, pnet.declarations.Transition]
        outarc = pnet.Arc(domains=domains, name='%s->%s' % ('start', light))
        pnet.add(outarc)
        pnet.connect(outarc, [outc, lightc['in']])
        inarc = pnet.Arc(domains=domains[::-1], name='%s->%s' % (light, 'start'))
        pnet.add(inarc)
        pnet.connect(inarc, [lightc['out'], inc])


    # Initial markings
    pnet.marking(start.uid).count = 1
    for light in lights:
        lightnet = pnet.find(light)
        red = lightnet.find('red')
        lightnet.marking(red.uid).count = 1
    
    return pnet
