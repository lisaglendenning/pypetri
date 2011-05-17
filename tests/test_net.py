# @copyright
# @license

import unittest
import itertools

from pypetri import net

#############################################################################
#############################################################################

class TestCaseNet(unittest.TestCase):
    
    Network = net.Network
    
    def build_linear(self, N=2):
        network = self.Network()
        conditions = [network.Condition() for i in xrange(N)]
        transitions = [network.Transition() for i in xrange(N-1)]
        arcs = []
        for i in xrange(N):
            if i > 0:
                pair = transitions[i-1], conditions[i]
                arc = network.Arc()
                net.link(arc, *pair)
                arcs.append(arc)
            if i < N-1:
                pair = conditions[i], transitions[i]
                arc = network.Arc()
                net.link(arc, *pair)
                arcs.append(arc)
        return network, conditions, transitions, arcs
    
    def initialize(self, conditions):
        conditions[0].marking = True

    def test_linear(self, N=2):
        network, conditions, transitions, arcs = self.build_linear(N)
        
        events = [e for e in network.next()]
        self.assertEqual(len(events), 0)
        
        self.initialize(conditions)
        
        for i in xrange(N-1):
            transition = transitions[i]
            events = [e for e in transition.next()]
            self.assertEqual(len(events), 1)
            events = [e for e in network.next()]
            self.assertEqual(len(events), 1)
            network()
            self.assertFalse(conditions[i].marking)
            self.assertTrue(conditions[i+1].marking)
            
        events = [e for e in network.next()]
        self.assertEqual(len(events), 0)

        return network

#############################################################################
#############################################################################
