# @copyright
# @license

import unittest
import itertools

from pypetri import net

#############################################################################
#############################################################################

class TestCaseNet(unittest.TestCase):
    
    Network = net.Network
    
    def build(self, N=2):
        network = self.Network()
        conditions = [network.Condition() for i in xrange(N)]
        transitions = [network.Transition() for i in xrange(N-1)]
        network.vertices.update(conditions)
        network.vertices.update(transitions)
        sequence = []
        for pair in itertools.izip(conditions, transitions):
            sequence.extend(pair)
        # and, since the lengths are uneven, the last condition
        sequence.append(conditions[-1])
        arcs = [a for a in network.chain(sequence)]
        self.assertEqual(len(arcs), N)
        
        return network, conditions, transitions, arcs
    
    def initialize(self, conditions):
        conditions[0].marking = True

    def test_linear(self, N=2):
        network, conditions, transitions, arcs = self.build(N)
        
        events = [e for e in network.next(transitions)]
        self.assertEqual(len(events), 0)
        
        self.initialize(conditions)
        
        for i in xrange(N-1):
            transition = transitions[i]
            events = [e for e in transition.next()]
            self.assertEqual(len(events), 1)
            events[0]()
            self.assertFalse(conditions[i].marking)
            self.assertTrue(conditions[i+1].marking)
            
        events = [e for e in network.next(transitions)]
        self.assertEqual(len(events), 0)

        return network

#############################################################################
#############################################################################
