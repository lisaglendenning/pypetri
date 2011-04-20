# @copyright
# @license

import pypetri.graph.net

import tests.test_net


#############################################################################
#############################################################################


class TestCaseNetGraph(tests.test_net.TestCaseNet):
    
    def test_static(self, network=None, conditions=None, transitions=None):
        if network is None:
            network = self.Network()
        if conditions is None:
            conditions = self.CONDITIONS
        if transitions is None:
            transitions = self.TRANSITIONS
        self.linearize(network, conditions, transitions)
        self.initialize(network)

        graph = pypetri.graph.net.NetworkGraph(network)

#############################################################################
#############################################################################
