# @copyright
# @license

import unittest

import pypetri.net

#############################################################################
#############################################################################


class TestCaseNet(unittest.TestCase):
    
    Network = pypetri.net.Network
    
    CONDITIONS = ['START', 'STOP',]
    START, STOP, = CONDITIONS
    TRANSITIONS = ['STOPPING']
    STOPPING, = TRANSITIONS
    
    def linearize(self, network, conditions, transitions):
        r"""Builds a linear network."""
        self.assertEqual(len(network), 0)
        
        for i,name in enumerate(conditions):
            cond = network.Condition(name=name)
            network.add(cond)
            self.assertEqual(len(network), i+1)
            self.assertEqual(len(network.conditions), i+1)
        
        for i,name in enumerate(transitions):
            trans = network.Transition(name=name)
            network.add(trans)
            self.assertEqual(len(network), len(conditions)+i+1)
            self.assertEqual(len(network.transitions), i+1)
        
        for i in xrange(len(conditions)-1):
            cond = [network[conditions[x]] for x in i,i+1]
            trans = network[transitions[i]]
            for j,pair in enumerate(((cond[0], trans,), (trans, cond[1],))):
                arc = network.connect(*pair)
                self.assertEqual(len(pair[0].outputs), 1)
                self.assertEqual(len(pair[1].inputs), 1)
                self.assertEqual(len(network.arcs), i+j+1)
                self.assertEqual(len(network), len(conditions)+len(transitions)+i+j+1)
                self.assertTrue(arc.source is pair[0])
                self.assertTrue(arc.sink is pair[1])
                
        return network
    
    def initialize(self, network):
        start = network[self.CONDITIONS[0]]
        start.marking = start.Marking()
        return network
    
    def test_linear(self, network=None, conditions=None, transitions=None):
        if network is None:
            network = self.Network()
        if conditions is None:
            conditions = self.CONDITIONS
        if transitions is None:
            transitions = self.TRANSITIONS
        self.linearize(network, conditions, transitions)
        
        enabled = [e for e in network.peek() if len(e.flows) > 0]
        self.assertEqual(len(enabled), 0)
        
        self.initialize(network)
        
        for i in xrange(len(conditions)-1):
            current = network[conditions[i]]
            next = network[conditions[i+1]]
            self.assertTrue(current.marking)
            self.assertFalse(next.marking)
            enabled = [e for e in network.peek() if len(e.flows) > 0]
            self.assertEqual(len(enabled), 1)
            output = network(enabled[0])
            self.assertFalse(current.marking)
            self.assertTrue(next.marking)

        enabled = [e for e in network.peek() if len(e.flows) > 0]
        self.assertEqual(len(enabled), 0)
        
        return network

#############################################################################
#############################################################################
