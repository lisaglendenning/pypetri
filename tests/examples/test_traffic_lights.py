# @copyright
# @license

import unittest

from pypetri.examples.traffic_lights import *

#############################################################################
#############################################################################

class TestCase(unittest.TestCase):
    
    Network = Network
    
    def initialized(self, network):
        for light in network.lights:
            events = [e for e in light.next()]
            self.assertEqual(len(events), 1)
    
    def test_example(self):
        network = self.Network()
        self.initialized(network)
        for light in network.lights:
            transitions = [getattr(light, name.lower()) for name in light.TRANSITIONS]
            for t in transitions:
                events = [e for e in t.next()]
                self.assertEqual(len(events), 1)
                output = t()
        self.initialized(network)

#############################################################################
#############################################################################
