# @copyright
# @license

import unittest

from pypetri.examples.network.link import *

#############################################################################
#############################################################################

class TestCase(unittest.TestCase):
    
    Network = Link
    
    def initialized(self, network):
        for q in (network.input, network.output,):
            self.assertEqual(len(q), 0)
        e = [e for e in network.next()]
        self.assertEqual(len(e), 0)
    
    def test_simple(self):
        network = self.Network()
        self.initialized(network)
        
        # Deliver
        input = (1,2)
        network.input.send(*input)
        self.assertEqual(tuple(network.input), input)
        output = input
        for i in output:
            network.deliver()
        self.assertEqual(len(network.input), 0)
        self.assertEqual(tuple(network.output), output)
        for i in output:
            self.assertEqual(network.output.head, i)
            network.output.dequeue()
        
        # Reorder
        input = (3,4)
        network.input.send(*input)
        self.assertEqual(tuple(network.input), input)
        output = tuple(reversed(input))
        network.delay()
        for i in output:
            network.deliver()
        self.assertEqual(len(network.input), 0)
        self.assertEqual(tuple(network.output), output)
        for i in output:
            self.assertEqual(network.output.head, i)
            network.output.dequeue()
            
        # Duplicate
        input = (5,6)
        network.input.send(*input)
        self.assertEqual(tuple(network.input), input)
        output = tuple(list(input) + [input[0]])
        network.duplicate()
        for i in input:
            network.deliver()
        self.assertEqual(len(network.input), 0)
        self.assertEqual(tuple(network.output), output)
        for i in output:
            self.assertEqual(network.output.head, i)
            network.output.dequeue()
        
        # Drop
        input = (7,8)
        network.input.send(*input)
        self.assertEqual(tuple(network.input), input)
        output = input[1:]
        network.drop()
        for i in output:
            network.deliver()
        self.assertEqual(len(network.input), 0)
        self.assertEqual(tuple(network.output), output)
        for i in output:
            self.assertEqual(network.output.head, i)
            network.output.dequeue()
            
        self.initialized(network)

#############################################################################
#############################################################################
