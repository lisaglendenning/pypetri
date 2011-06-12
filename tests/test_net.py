# @copyright
# @license

import unittest
import itertools

from pypetri.net import *

#############################################################################
#############################################################################

class TestCaseNet(unittest.TestCase):
    
    class Network(Network):
        
        def Transition(self, *args, **kwargs):
            if 'pipe' not in kwargs:
                kwargs['pipe'] = operators.Pipeline(operators.Iter(), operators.Call())
            return super(TestCaseNet.Network, self).Transition(*args, **kwargs)
    
    def build_linear(self, network, N=2):
        conditions = [network.Condition() for i in xrange(N)]
        transitions = [network.Transition() for i in xrange(N-1)]
        arcs = []
        for i in xrange(N):
            if i > 0:
                pair = transitions[i-1], conditions[i]
                arcs.append(network.Arc(*pair))
            if i < N-1:
                pair = conditions[i], transitions[i]
                arcs.append(network.Arc(*pair))
        return conditions, transitions, arcs
    
    def initialize(self, conditions):
        conditions[0].marking = True

    def isdone(self, network):
        events = [e for e in network.next()]
        self.assertEqual(len(events), 0)

    def test_linear(self, N=2):
        network = self.Network()
        conditions, transitions, arcs = self.build_linear(network, N)
        
        self.isdone(network)
        
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
        
        self.isdone(network)

        return network

#############################################################################
#############################################################################
