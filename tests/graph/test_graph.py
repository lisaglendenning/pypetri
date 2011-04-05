# @copyright
# @license

import unittest
import random

import pypetri.trellis as trellis
import pypetri.graph.graph as pgraph

#############################################################################
#############################################################################

class GraphListener(trellis.Component):
    
    N = 64
    
    def __init__(self, graph):
        self.graph = graph
        self.action = None
    
    def step(self):
        graph = self.graph
        N = self.N
        
        # Possible actions
        actions = []
        if len(graph) > 0:
            actions.append((graph.REMOVE_ACTION, graph.NODE_TYPE))
        maxed = N
        if len(graph) < maxed:
            actions.append((graph.ADD_ACTION, graph.NODE_TYPE))
        if graph.size() > 0:
            actions.append((graph.REMOVE_ACTION, graph.EDGE_TYPE))
        maxed = len(graph)
        maxed *= (maxed - 1) / 2
        if graph.size() < maxed:
            actions.append((graph.ADD_ACTION, graph.EDGE_TYPE))
        assert len(actions) > 0
        
        # Random action
        r = random.choice(actions)
        args = ()
        kwargs = {}
    
        if r[0] == graph.REMOVE_ACTION:
            if r[1] == graph.NODE_TYPE:
                args = (random.choice(graph.nodes()),)
            else:
                args = random.choice(graph.edges())
        else:
            if r[1] == graph.NODE_TYPE:
                available = set(xrange(N)) - set(graph.nodes())
                args = (random.choice(list(available)),)
            else:
                # pick a random node that is incomplete
                nodes = [n for n in graph if graph.degree(n) < N - 1]
                node = random.choice(nodes)
                # pick a random second node that is not a neighbor
                available = set(xrange(N)) - set(graph.neighbors(n)) - set([node])
                args = (node, random.choice(list(available)))
        self.action = (r[0], r[1], args, kwargs)
        
        if self.action[0] == graph.REMOVE_ACTION:
            if self.action[1] == graph.NODE_TYPE:
                graph.remove_node(*self.action[2], **self.action[3])
                assert not graph.has_node(self.action[2][0])
            else:
                graph.remove_edge(*self.action[2], **self.action[3])
                assert not graph.has_edge(*self.action[2][:2])
        else:
            if self.action[1] == graph.NODE_TYPE:
                graph.add_node(*self.action[2], **self.action[3])
                assert graph.has_node(self.action[2][0])
            else:
                graph.add_edge(*self.action[2], **self.action[3])
                assert graph.has_edge(*self.action[2][:2])
        self.action = None
    
    @trellis.maintain
    def verify(self):
        if self.graph is not None:
            changes = self.graph.changes
            if changes:
                assert len(changes) == 1
                assert changes[0] == self.action

#############################################################################
#############################################################################

class TestCaseGraph(unittest.TestCase):
    
    def test_graph(self, N=4):
        graph = pgraph.Graph()
        listener = GraphListener(graph)
        for i in xrange(listener.N):
            listener.step()
        listener.graph = None
        graph.clear()
        self.assertEqual(len(graph), 0)

#############################################################################
#############################################################################
