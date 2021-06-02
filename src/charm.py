#!/usr/bin/env python3
# Copyright 2021 Ubuntu
# See LICENSE file for licensing details.
#
# Learn more at: https://juju.is/docs/sdk

"""Charm the service.

Refer to the following post for a quick-start guide that will help you
develop a new k8s charm using the Operator Framework:

    https://discourse.charmhub.io/t/4208
"""

import logging
import os

from ops.charm import CharmBase
from ops.framework import StoredState
from ops.main import main
from ops.model import ActiveStatus

from charms.nginx_ingress_integrator.v0.ingress import IngressRequires

logger = logging.getLogger(__name__)


class GitlabCEOperatorCharm(CharmBase):
    """Charm the service."""

    _stored = StoredState()

    def __init__(self, *args):
        super().__init__(*args)
        self.framework.observe(self.on.config_changed, self._on_config_changed)
        self._stored.set_default(things=[])

        self.ingress = IngressRequires(self, self.ingress_config)

    def charm_dir(self):
        """Return the root directory of the current charm"""
        d = os.environ.get('JUJU_CHARM_DIR')
        if d is not None:
            return d
        return os.environ.get('CHARM_DIR')

    def isfloat(self, value):
        try:
            float(value)
            return True
        except ValueError:
            return False

    def format_config_value(self, value):
        val = str(value)
        if isinstance(value, bool):
            if value:
                val = "true"
            else:
                val = "false"
        elif val.isdigit():
            val = int(val)
        elif self.isfloat(val):
            val = float(val)
        else:
            val = "'{}'".format(val)
        return val

    def _compose_gitlab_config(self):
        cfg = self.model.config
        cfg_terms = []

        # build external url
        exturl = None
        if cfg.get('external_url'):
            exturl = cfg.get('external_url')
            if exturl != '' and not exturl.startswith("http"):
                exturl = "http://" + exturl

        http_port = cfg.get('http_port')
        if exturl is not None and http_port is not None:
            if exturl.endswith("/"):
                exturl = exturl[:-1]

            exturl = exturl + ":{}".format(http_port)

        if exturl is not None:
            cfg_terms = ['external_url {}'.format(self.format_config_value(exturl))]

        # disable internal monitoring and alerting services
        cfg_terms += ['alertmanager[\'enable\']=false']
        cfg_terms += ['prometheus[\'enable\']=false']

        def append_config(cfg_terms, k, v):
            if v is None or str(v) == '':
                return
            cfg_terms += ['{}={}'.format(k, self.format_config_value(v))]

        append_config(cfg_terms, 'gitlab_rails[\'gitlab_ssh_host\']',
                      cfg.get('ssh_host')),
        append_config(cfg_terms, 'gitlab_rails[\'time_zone\']',
                      cfg.get('time_zone')),
        append_config(cfg_terms, 'gitlab_rails[\'gitlab_email_from\']',
                      cfg.get('email_from')),
        append_config(cfg_terms, 'gitlab_rails[\'gitlab_email_display_name\']',
                      cfg.get('from_email_name')),
        append_config(cfg_terms, 'gitlab_rails[\'gitlab_email_reply_to\']',
                      cfg.get('reply_to_email')),
        append_config(cfg_terms, 'gitlab_rails[\'smtp_enable\']',
                      cfg.get('smtp_enable')),
        append_config(cfg_terms, 'gitlab_rails[\'smtp_address\']',
                      cfg.get('smtp_address')),
        append_config(cfg_terms, 'gitlab_rails[\'smtp_port\']',
                      cfg.get('smtp_port')),
        append_config(cfg_terms, 'gitlab_rails[\'smtp_user_name\']',
                      cfg.get('smtp_user_name')),
        append_config(cfg_terms, 'gitlab_rails[\'smtp_password\']',
                      cfg.get('smtp_password')),
        append_config(cfg_terms, 'gitlab_rails[\'smtp_domain\']',
                      cfg.get('smtp_domain')),
        append_config(cfg_terms, 'gitlab_rails[\'smtp_enable_starttls_auto\']',
                      cfg.get('smtp_enable_starttls_auto')),
        append_config(cfg_terms, 'gitlab_rails[\'smtp_tls\']',
                      cfg.get('smtp_tls')),

        return '; '.join(map(str, cfg_terms))

    def _on_config_changed(self, _):
        container = self.unit.get_container("gitlab")
        layer = self._gitlab_layer()
        services = container.get_plan().to_dict().get("services", {})
        if services != layer["services"]:
            container.add_layer("gitlab", layer, combine=True)
            logger.info("Added updated layer to gitlab")
            if container.get_service("gitlab").is_running():
                container.stop("gitlab")
            # Custom /assets/wrapper for Gitlab initial configuration
            file = open(os.path.join(self.charm_dir(), 'templates/gitlab-install'), 'r')
            container.push("/assets/gitlab-install", file, make_dirs=True, permissions=0o755)
            container.start("gitlab")
            logger.info("Restarted gitlab service")
        self.unit.status = ActiveStatus()

    def _gitlab_layer(self):
        conf = self._compose_gitlab_config()
        logger.debug("GITLAB_OMNIBUS_CONFIG %s", conf)
        return {
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

    @property
    def ingress_config(self):
        cfg = self.model.config
        ext_url = cfg.get('external_url')
        http_port = cfg.get('http_port')
        if not ext_url:
            ext_url = 'gitlab-ce.juju'
        if not http_port:
            http_port = 80

        ingress_config = {
            "service-hostname": ext_url,
            "service-name": self.app.name,
            "service-port": http_port,
        }
        tls_secret_name = self.model.config["tls_secret_name"]
        if tls_secret_name:
            ingress_config["tls-secret-name"] = tls_secret_name
        return ingress_config


if __name__ == "__main__":
    main(GitlabCEOperatorCharm)
