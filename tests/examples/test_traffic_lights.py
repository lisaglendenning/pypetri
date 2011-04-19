# @copyright
# @license

import unittest

import examples.traffic_lights as traffic_lights

#############################################################################
#############################################################################

class TestCaseTrafficLights(unittest.TestCase):
    
    def test_example(self):
        network = traffic_lights.TwoWayIntersection.create()
        enabled = [e for e in network.search()]
        self.assertEqual(len(enabled), 2)
        
        for l in network.LIGHTS:
            light = network.find(l)
            
            for t in light.TRANSITIONS:
                trans = light.find(t)
                enabled = [e for e in trans.search()]
                self.assertEqual(len(enabled), 1)
                output = network(enabled[0])

        enabled = [e for e in network.search()]
        self.assertEqual(len(enabled), 2)

#############################################################################
#############################################################################
