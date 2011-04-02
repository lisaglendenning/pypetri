# @copyright
# @license

import unittest

import examples.traffic_lights as traffic_lights

#############################################################################
#############################################################################

class TestCaseTrafficLights(unittest.TestCase):
    
    def test_example(self):
        network = traffic_lights.create()
        start = network.find(traffic_lights.START)
        
        for light in traffic_lights.LIGHTS:
            lightnet = network.find(light)
            
            for t in traffic_lights.TRANSITIONS:
                trans = lightnet.find(t)
                enabled = [e for e in trans.enabled()]
                self.assertEqual(len(enabled), 1)
                network.step(enabled)

#############################################################################
#############################################################################
