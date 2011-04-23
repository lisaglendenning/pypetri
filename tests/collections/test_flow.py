# @copyright
# @license

import unittest
import itertools

from .. import test_net
from pypetri.collections import flow

#############################################################################
#############################################################################

class TestCaseFlow(test_net.TestCaseNet):
    
    Network = flow.Network
    
    def initialize(self, conditions):
        conditions[0].marking = 1

#############################################################################
#############################################################################
