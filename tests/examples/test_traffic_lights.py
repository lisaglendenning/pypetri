# @copyright
# @license

import unittest

import examples.traffic_lights as traffic_lights

#############################################################################
#############################################################################

class TestCaseTrafficLights(unittest.TestCase):
    
    def test_example(self):
        network = traffic_lights.create()
        enabled = [e for e in network.peek()]
        self.assertEqual(len(enabled), 2)
        
        for l in network.LIGHTS:
            light = network.find(l)
            
            for t in light.TRANSITIONS:
                enabled = [e for e in light.peek()]
                self.assertEqual(len(enabled), 1)
                output = network(enabled[0])

        enabled = [e for e in network.peek()]
        self.assertEqual(len(enabled), 2)

#############################################################################
#############################################################################
