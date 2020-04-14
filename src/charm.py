#!/usr/bin/env python3

import subprocess
import logging
import sys

sys.path.append('lib') # noqa

from ops.framework import (
    EventBase,
    EventSource,
    StoredState,
)

from ops.model import ActiveStatus, MaintenanceStatus

from ops.charm import CharmBase, CharmEvents

from ops.main import main
from pathlib import Path

from jinja2 import Environment, FileSystemLoader
from peers import KeepalivedPeers
from interface_vrrp_parameters import VRRPParametersRequires

logger = logging.getLogger(__name__)


class KeepalivedInitializedEvent(EventBase):
    pass


class KeepalivedEvents(CharmEvents):
    keepalived_initialized = EventSource(KeepalivedInitializedEvent)


class KeepalivedCharm(CharmBase):

    on = KeepalivedEvents()
    state = StoredState()

    def __init__(self, *args):
        super().__init__(*args)

        self.keepalived_conf_file = Path(f'/etc/keepalived/juju-{self.app.name}.cfg')
        self.service_name = f'juju-{self.app.name}'
        self.keepalived_service_file = Path(f'/etc/systemd/system/{self.service_name}.service')

        self.framework.observe(self.on.install, self.on_install)
        self.framework.observe(self.on.upgrade_charm, self.on_upgrade_charm)
        self.peers = KeepalivedPeers(self, 'keepalived-peers')
        self.primary = VRRPParametersRequires(self, 'vrrp-parameters')
        self.framework.observe(self.primary.on.primary_changed, self.on_primary_changed)

    def on_install(self, event):
        subprocess.check_call(['apt', 'update'])
        subprocess.check_call(['apt', 'install', '-yq', 'keepalived'])
        self.on.keepalived_initialized.emit()
        self.unit.status = MaintenanceStatus('Waiting for a primary app unit to provide'
                                             ' VRRP instance parameters.')

    def on_upgrade_charm(self, event):
        self.update_config()

    def on_primary_changed(self, event):
        self.update_config()

    def update_config(self):
        config_ctxt = {
            'is_initial': self.peers.initial_unit == self.model.unit.name,
            'vrrp_instances': self.primary.vrrp_instances
        }
        env = Environment(loader=FileSystemLoader('templates'))
        config_template = env.get_template('keepalived.conf.j2')
        self.keepalived_conf_file.write_text(config_template.render(config_ctxt))

        service_ctxt = {
            'keepalived_config': self.keepalived_conf_file
        }
        service_template = env.get_template('keepalived.service.j2')
        self.keepalived_service_file.write_text(service_template.render(service_ctxt))
        subprocess.check_call(['systemctl', 'daemon-reload'])
        subprocess.check_call(['systemctl', 'restart', self.service_name])
        self.unit.status = ActiveStatus()


if __name__ == '__main__':
    main(KeepalivedCharm)
