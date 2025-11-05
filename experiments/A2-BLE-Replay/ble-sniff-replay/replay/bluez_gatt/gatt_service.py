from dbus_next.service import (
    ServiceInterface, method, dbus_property, PropertyAccess)


class GATTService(ServiceInterface):
    def __init__(self, path, uuid, primary=True):
        # https://git.kernel.org/pub/scm/bluetooth/bluez.git/tree/doc/org.bluez.GattService.rst
        super().__init__("org.bluez.GattService1")
        self._path = path
        self._uuid = uuid
        self._primary = primary

    # has to be set on read only based on bluez doc
    @dbus_property(access=PropertyAccess.READ)
    def UUID(self) -> "s":  # s is the D-Bus type signature for string  # type: ignore
        return self._uuid

    # has to be set on read only based on bluez doc
    @dbus_property(access=PropertyAccess.READ)
    def Primary(self) -> "b":  # type: ignore
        return self._primary
