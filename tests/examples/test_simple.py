# @copyright
# @license

import tests.test_net

import examples.simple as simple

#############################################################################
#############################################################################


class TestCaseSimple(tests.test_net.TestCaseNet):
    
    Network = simple.SimpleNetwork
    
    def initialize(self, network):
        start = network[self.CONDITIONS[0]]
        start.marking.count = 1
        return network
        
    def test_linear(self, network=None, conditions=None, transitions=None):
        network = super(TestCaseSimple, self).test_linear(network, conditions, transitions)
        start = network[self.CONDITIONS[0]]
        stop = network[self.CONDITIONS[-1]]
        self.assertEqual(start.marking.count, 0)
        self.assertEqual(stop.marking.count, 1)
        return network

#############################################################################
#############################################################################
