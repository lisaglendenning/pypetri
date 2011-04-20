
import pypetri.graph.net

SHAPE = 'shape'
SHAPES = { pypetri.graph.net.NetworkGraph.CONDITION: 'ellipse', 
           pypetri.graph.net.NetworkGraph.TRANSITION: 'box',
           pypetri.graph.net.NetworkGraph.NETWORK: 'doubleoctagon',
         }

def markup(network, graph=None):
    if graph is None:
        graph = network.snapshot()
    for u in graph:
        role = graph.node[u][pypetri.graph.net.NetworkGraph.ROLE]
        if role in SHAPES:
            graph.node[u][SHAPE] = SHAPES[role]
    return graph
