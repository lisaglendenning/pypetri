# @copyright
# @license

import unittest
import itertools

from .. import test_net
from pypetri import operators
from pypetri.collections import flow

#############################################################################
#############################################################################

class TestCaseFlow(test_net.TestCaseNet):
    
    class Network(flow.Network):
        
        def Transition(self, *args, **kwargs):
            if 'pipe' not in kwargs:
                kwargs['pipe'] = operators.Pipeline(operators.Iter(), operators.Call())
            return super(TestCaseFlow.Network, self).Transition(*args, **kwargs)
    
    def initialize(self, conditions):
        conditions[0].marking = 1

#############################################################################
#############################################################################
