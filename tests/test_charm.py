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

    def test_external_url(self):
        self.assertEqual(self.harness.charm._external_url, "gitlab-ce")

    def test_ingress_config(self):
        expected = {
            "service-hostname": "gitlab-ce",
            "service-name": "gitlab-ce",
            "service-port": 80,
        }
        self.assertEqual(self.harness.charm.ingress_config, expected)
        # And now test with a TLS secret name set.
        self.harness.disable_hooks()
        self.harness.update_config({"tls_secret_name": "gitlab-tls"})
        expected["tls-secret-name"] = "gitlab-tls"
        self.assertEqual(self.harness.charm.ingress_config, expected)

    def test_gitlab_layer(self):
        conf = ("external_url 'http://gitlab-ce:80'; "
                "alertmanager['enable']=false; "
                "prometheus['enable']=false; "
                "gitlab_rails['smtp_enable']=true; "
                "gitlab_rails['smtp_enable_starttls_auto']=true; "
                "gitlab_rails['smtp_tls']=false")
        expected = {
            "summary": "gitlab layer",
            "description": "pebble config layer for gitlab",
            "services": {
                "gitlab": {
                    "override": "replace",
                    "summary": "gitlab",
                    "command": "bash -c \"/assets/gitlab-install\"",
                    "startup": "enabled",
                    "environment": {"GITLAB_OMNIBUS_CONFIG": conf},
                }
            },
        }
        self.assertEqual(self.harness.charm._gitlab_layer(), expected)
