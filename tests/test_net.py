# @copyright
# @license

import unittest

import examples.simple as simple

#############################################################################
#############################################################################


class TestCaseNet(unittest.TestCase):
    
    def test_net(self):
        network = simple.SimpleNetwork()
        
        start = network.Condition(name='start')
        network.add(start)
        stop = network.Condition(name='stop')
        network.add(stop)
        stopping = network.Transition(name='stopping')
        network.add(stopping)
        
        network.connect(start, stopping)
        network.connect(stopping, stop)
        
        start.marking.count = 1
        
        enabled = [e for e in stopping.enabled()]
        self.assertEqual(len(enabled), 1)
        
        network.step(enabled)
        self.assertEqual(start.marking.count, 0)
        self.assertEqual(stop.marking.count, 1)

#############################################################################
#############################################################################
