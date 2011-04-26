# @copyright
# @license

import unittest

import examples.traffic_lights as traffic_lights

#############################################################################
#############################################################################

class TestCaseTrafficLights(unittest.TestCase):
    
    def initialized(self, network):
        for light in network.lights:
            events = [e for e in light.next(light.transitions)]
            self.assertEqual(len(events), 1)
    
    def test_example(self):
        network = traffic_lights.Network()
        self.initialized(network)
        for light in network.lights:
            for t in light.transitions:
                events = [e for e in t.next()]
                self.assertEqual(len(events), 1)
                output = events[0]()
        self.initialized(network)

#############################################################################
#############################################################################
