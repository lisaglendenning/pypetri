# @copyright
# @license

from pypetri.graph.net import *

from .. import test_net

#############################################################################
#############################################################################

class TestCase(test_net.TestCaseNet):
    
    def test_linear(self, N=2):
        network = self.Network()
        conditions, transitions, arcs = self.build_linear(network, N)
        self.initialize(conditions)

        def toname(v):
            return str(id(v))

        graphed = NetworkGraph(network, toname)
        g = graphed.graph.snapshot()
        self.assertEqual(g.order(), 2*N-1)
        self.assertEqual(g.size(), 2*N-2)

#############################################################################
#############################################################################
