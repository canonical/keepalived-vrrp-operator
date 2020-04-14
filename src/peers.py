from ops.framework import Object, StoredState


class KeepalivedPeers(Object):

    state = StoredState()

    def __init__(self, charm, relation_name):
        super().__init__(charm, relation_name)
        self._relation_name = relation_name
        self._relation = self.framework.model.get_relation(self._relation_name)
        self.framework.observe(charm.on.keepalived_initialized, self)

    @property
    def is_joined(self):
        return self._relation is not None

    def on_keepalived_initialized(self, event):
        if not self.framework.model.unit.is_leader():
            return
        # A workaround for LP: #1859769.
        if not self.is_joined:
            event.defer()
            return
        self._relation.data[self.model.app]['initial_unit'] = self.framework.model.unit.name

    @property
    def initial_unit(self):
        """Return the unit that is supposed to have an initial MASTER state."""
        if self.is_joined:
            return self._relation.data[self.model.app].get('initial_unit')
        else:
            return None
