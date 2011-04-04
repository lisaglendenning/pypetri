# @copyright
# @license

import unittest

import examples.traffic_lights as traffic_lights

#############################################################################
#############################################################################

class TestCaseTrafficLights(unittest.TestCase):
    
    def test_example(self):
        network = traffic_lights.TwoWayIntersection.create()
        start = network.find(network.START)
        
        for l in network.LIGHTS:
            light = network.find(l)
            
            for t in light.TRANSITIONS:
                trans = light.find(t)
                enabled = [e for e in trans.enabled()]
                self.assertEqual(len(enabled), 1)
                network.step(enabled)

#############################################################################
#############################################################################
