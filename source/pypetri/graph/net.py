# @copyright
# @license

import networkx as nx

import pypetri.net as pnet
import pypetri.hub as phub

import pypetri.graph.hub

#############################################################################
#############################################################################

Graph = nx.MultiDiGraph
    
class NetworkGraph(pypetri.graph.hub.HubGraph):

    
    def snapshot(self):
        graph, subgraphs = super(NetworkGraph, self).snapshot()
        
        netgraph = Graph(name=self.name)
        
        Arc = self.hub.Arc
        Condition = self.hub.Condition
        Transition = self.hub.Transition
        
        arcs = set()
        conditions = set()
        transitions = set()
        hubs = set()
        for hub in self.inferiors.itervalues():
            if isinstance(hub, Arc):
                arcs.add(hub)
            elif isinstance(hub, Condition):
                conditions.add(hub)
            elif isinstance(hub, Transition):
                transitions.add(hub)
            else:
                hubs.add(hub)
        
        for nodes, type in ((conditions, 'Condition',),
                            (transitions, 'Transition'),
                            (hubs, 'Hub'),):
            for hub in nodes:
                netgraph.add_node(hub.uid, name=hub.name)
        
        for arc in arcs:
            nodes = [arc.source, arc.sink]
            assert None not in nodes
            for i in xrange(len(nodes)):
                while nodes[i].superior is not self.hub:
                    assert nodes[i].superior is not None
                    nodes[i] = nodes[i].superior
                assert nodes[i].uid in netgraph
            netgraph.add_edge(nodes[0].uid,
                              nodes[1].uid,
                              name=arc.name)
        
        return netgraph, subgraphs

    def dotgraph(self):
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
