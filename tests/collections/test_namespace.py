# @copyright
# @license

import unittest

from pypetri.collections import namespace

#############################################################################
#############################################################################

class TestCaseNamable(unittest.TestCase):
    
    def Namable(self, cls, *args, **kwargs):
        named = cls(*args, **kwargs)
        self.assertTrue(named.top is named)
        self.assertTrue(named.domain is None)
        return named
    
    def test_namespace(self, N=2):
        top = self.Namable(namespace.Namespace)
        self.assertFalse(top.name)
        
        nodes = [self.Namable(namespace.Namable, name=i) for i in xrange(1, N+1)]
        for i, x in enumerate(nodes):
            self.assertEqual(x.name, i+1)
            top.add(x)
            self.assertTrue(x.name in top)
            self.assertTrue(x.domain is top)
            self.assertTrue(x.top is top)
            self.assertTrue(x is top.find(x.uid))

#############################################################################
#############################################################################
