# @copyright
# @license

import pypetri.graph.net

from .. import test_net


#############################################################################
#############################################################################


class TestCaseNetGraph(test_net.TestCaseNet):
    
    def test_linear(self, N=2):
        network, conditions, transitions, arcs = self.build(N)
        self.initialize(conditions)

        graphed = pypetri.graph.net.GraphNetwork(network)
        g = graphed.snapshot()
        self.assertEqual(g.order(), 2*N-1)
        self.assertEqual(g.size(), 2*N-2)

#############################################################################
#############################################################################
