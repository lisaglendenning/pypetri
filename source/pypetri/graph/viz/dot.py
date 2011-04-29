
import pypetri.graph.net

SHAPE = 'shape'
SHAPES = { 'Condition': 'ellipse', 
           'Transition': 'box',
           'Network': 'doubleoctagon',
         }

def markup(network, graph=None, shapes=None):
    if shapes is None:
        shapes = SHAPES
    if graph is None:
        graph = network.snapshot()
    for u in graph:
        v = network.vertices[u]
        for role in [getattr(network.net, k) for k in shapes]:
            if isinstance(v, role):
                graph.node[SHAPE] = shapes[role]
    return graph
