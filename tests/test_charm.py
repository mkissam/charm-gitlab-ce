# Copyright 2021 Ubuntu
# See LICENSE file for licensing details.
#
# Learn more about testing at: https://juju.is/docs/sdk/testing

import unittest

from charm import GitlabCEOperatorCharm
from ops.testing import Harness


class TestCharm(unittest.TestCase):
    def setUp(self):
        self.harness = Harness(GitlabCEOperatorCharm)
        self.addCleanup(self.harness.cleanup)
        self.harness.begin()
