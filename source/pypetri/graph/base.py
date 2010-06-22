
import warnings
warnings.simplefilter("ignore", DeprecationWarning)

from peak.events import trellis

import networkx as nx

import pypetri.base as pbase
import pypetri.hub as phub

#############################################################################
#############################################################################

class CollectiveGraph(trellis.Component):

    hubgraph = trellis.attr(None)

    def __init__(self, hubgraph, **kwargs):
        super(CollectiveGraph, self).__init__(hubgraph=hubgraph, **kwargs)

    def snapshot(self):
        root = self.hubgraph.hub.root
        hubgraph = self.hubgraph.snapshot()
        
        # first, remove any collectives
        nbunch = []
        for n in hubgraph.nodes_iter():
            obj = root.get(n)
            if isinstance(obj, pbase.BaseCollective):
                nbunch.append(n)
        hubgraph.remove_nodes_from(nbunch)
        
        # next, fold connectors
        nbunch = []
        ebunch = []
        for u in hubgraph.nodes_iter():
            obj = root.get(u)
            if isinstance(obj, phub.Connector):
                nbunch.append(u)
                hub = obj.superior.uid
                for v in hubgraph.neighbors_iter(u):
                    if v == hub:
                        continue
                    ebunch.append((hub,v))
        hubgraph.remove_nodes_from(nbunch)
        hubgraph.add_edges_from(ebunch)
        
        # now, convert to a directed graph
        graph = nx.DiGraph()
        
        # add transitions, conditions, and arcs
        for u in hubgraph.nodes_iter():
            obj = root.get(u)
            attrs = {}
            if isinstance(obj, root.declarations.Condition):
                attrs['shape'] = 'ellipse'
            elif isinstance(obj, root.declarations.Transition):
                attrs['shape'] = 'box'
            elif isinstance(obj, root.declarations.Arc):
                u = obj.traverse(0)
                v = obj.traverse(1)
                if u and v:
                    u = u[1]
                    v = v[1]
                    graph.add_edge(u, v, attrs)
                continue
            else:
                continue
            graph.add_node(u, attrs)
        
        return graph

#############################################################################
#############################################################################
