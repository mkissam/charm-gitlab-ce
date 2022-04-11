# Copyright 2021 Ubuntu
# See LICENSE file for licensing details.
#
# Learn more about testing at: https://juju.is/docs/sdk/testing

import json
import os
import unittest
from unittest import mock

import charm
from ops import model
from ops.testing import Harness


class TestCharm(unittest.TestCase):

    @mock.patch("charm.k8s_svc_patch.KubernetesServicePatch", lambda x, y: None)
    def setUp(self, *unused):
        self.harness = Harness(charm.GitlabCECharm)
        self.addCleanup(self.harness.cleanup)
        self.harness.begin()

    def _patch(self, obj, method, *args, **kwargs):
        """Patches the given method and returns its Mock."""
        patcher = mock.patch.object(obj, method, *args, **kwargs)
        mock_patched = patcher.start()
        self.addCleanup(patcher.stop)

        return mock_patched

    def _add_relation(self, relation_name, relator_name, relation_data):
        """Adds a relation to the charm."""
        relation_id = self.harness.add_relation(relation_name, relator_name)
        self.harness.add_relation_unit(relation_id, "%s/0" % relator_name)

        self.harness.update_relation_data(relation_id, relator_name, relation_data)
        return relation_id

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

    def test_gitlab_relation(self):
        """Adds a unit test for the gitlab relation.

        When relating a charm to this gitlab-ce charm, this charm should
        create a new token for the related charm.
        """
        # Setting the leader will allow this charm to write into the
        # relation data.
        self.harness.set_leader(True)

        # Create the necessary mocks and make the charm Active.
        os.environ["CHARM_DIR"] = "/foo"
        self._patch(
            charm, "open", mock.mock_open(read_data=""), create=True
        )
        container = self.harness.model.unit. get_container("gitlab")
        self._patch(container, "push")
        self._patch(container, "start")

        self.harness.update_config({"tls_secret_name": "gitlab-tls"})

        self.assertEqual(self.harness.model.unit.status, model.ActiveStatus())

        # Add the gitlab relation and expect that the token is created and set
        # into the relation data.
        mock_token = "test-uuid"
        self._patch(charm.uuid, "uuid4", return_value=mock_token)
        mock_exec = self._patch(container, "exec")

        self._add_relation(
            charm.GITLAB_RELATION_NAME, "client-charm", {}
        )

        rails_cmd = charm.RAILS_CREATE_TOKEN % {
            "username": "root",
            "token_name": "client-charm",
            "token": mock_token,
        }
        mock_exec.assert_called_once_with(
            ["gitlab-rails", "runner", rails_cmd]
        )
        relation = self.harness.charm.model.relations[
            charm.GITLAB_RELATION_NAME
        ][0]
        expected_credentials = {
            "host": self.harness.charm._external_url,
            "port": 80,
            "api-scheme": charm.SCHEME_HTTPS,
            "access-token": mock_token,
        }
        expected_data = {"credentials": json.dumps(expected_credentials)}
        self.assertEqual(expected_data, relation.data[self.harness.charm.app])

        # Remove the relation, assert that the token is revoked.
        mock_exec.reset_mock()
        self.harness.remove_relation(relation.id)

        rails_cmd = charm.RAILS_DELETE_TOKEN % {"token": mock_token}
        mock_exec.assert_called_once_with(
            ["gitlab-rails", "runner", rails_cmd]
        )
