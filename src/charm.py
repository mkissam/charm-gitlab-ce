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
from ops.main import main
from ops.model import ActiveStatus
from ops.pebble import ConnectionError

from charms.nginx_ingress_integrator.v0.ingress import IngressRequires

logger = logging.getLogger(__name__)


class GitlabCEOperatorCharm(CharmBase):
    """Charm the service."""

    def __init__(self, *args):
        super().__init__(*args)
        self.framework.observe(self.on.config_changed, self._on_config_changed)

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
        exturl = self._external_url
        if exturl != '' and not exturl.startswith("http"):
            exturl = "http://" + exturl

        http_port = cfg.get('http_port')
        if exturl.endswith("/"):
            exturl = exturl[:-1]

        exturl = exturl + ":{}".format(http_port)

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

    def _on_config_changed(self, event):
        container = self.unit.get_container("gitlab")
        layer = self._gitlab_layer()
        try:
            services = container.get_plan().to_dict().get("services", {})
        except ConnectionError:
            logger.info("Unable to connect to Pebble, deferring event")
            event.defer()
            return
        # Update our ingress definition if appropriate.
        self.ingress.update_config(self.ingress_config)
        if services != layer["services"]:
            container.add_layer("gitlab", layer, combine=True)
            logger.info("Added updated layer to gitlab")
            if container.get_service("gitlab").is_running():
                container.stop("gitlab")
            # Custom /assets/wrapper for Gitlab initial configuration
            with open(os.path.join(self.charm_dir(), 'templates/gitlab-install'), 'r') as file:
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
    def _external_url(self):
        return self.config.get("external_url") or self.app.name

    @property
    def ingress_config(self):
        ingress_config = {
            "service-hostname": self._external_url,
            "service-name": self.app.name,
            "service-port": self.config["http_port"],
        }
        tls_secret_name = self.config["tls_secret_name"]
        if tls_secret_name:
            ingress_config["tls-secret-name"] = tls_secret_name
        return ingress_config


if __name__ == "__main__":
    main(GitlabCEOperatorCharm)
