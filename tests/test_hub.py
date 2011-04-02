# @copyright
# @license

import unittest

import pypetri.hub

#############################################################################
#############################################################################

class TestCaseHub(unittest.TestCase):
    
    def test_hub(self, N=4):
        hubba = pypetri.hub.Hub()
        connectors = [pypetri.hub.Connector(name=i) for i in xrange(N)]
        for i, c in enumerate(connectors):
            self.assertEqual(c.name, i)
            hubba.add(c)
        for c in connectors:
            self.assertTrue(c is hubba.find(c.uid))
            self.assertFalse(c.connected)
        for i in xrange(0, N, 2):
            c1 = connectors[i]
            c2 = connectors[i+1]
            c1.connect(c2)
            self.assertTrue(c1.connected)
            self.assertTrue(c2.connected)
            self.assertTrue(c1.peer is c2)
            self.assertTrue(c2.peer is c1)
            self.assertTrue(hubba.traverse(c1.uid) is c2)
            self.assertTrue(hubba.traverse(c2.uid) is c1)
        for i in xrange(0, N, 2):
            c1 = connectors[i]
            c2 = connectors[i+1]
            c1.disconnect()
            self.assertFalse(c1.connected)
            self.assertFalse(c2.connected)

#############################################################################
#############################################################################
