from dbus_next.service import (
    ServiceInterface, method, dbus_property, PropertyAccess)


class Advertisement(ServiceInterface):
    '''
    Create an Advertisement on BlueZ interface to have it be discoverable
    Source: https://git.kernel.org/pub/scm/bluetooth/bluez.git/tree/doc/org.bluez.LEAdvertisement.rst
    '''

    def __init__(self, path: str, local_name: str, service_uuids: list[str]):
        super().__init__("org.bluez.LEAdvertisement1")
        self._path = path
        self._local_name = local_name
        self._service_uuids = service_uuids

    @dbus_property(access=PropertyAccess.READ)
    def Type(self) -> "s":  # type: ignore
        return "peripheral"  # possible values according to doc "broadcast" or "peripheral"

    @dbus_property(access=PropertyAccess.READ)
    def ServiceUUIDs(self) -> "as":  # type: ignore
        return self._service_uuids

    @dbus_property(access=PropertyAccess.READWRITE)
    def LocalName(self) -> "s":  # type: ignore
        return self._local_name

    @LocalName.setter
    def LocalName(self, value: "s"):  # type: ignore
        self._local_name = value

    @dbus_property(access=PropertyAccess.READWRITE)
    def TxPower(self) -> "n":  # type: ignore
        return 0

    @TxPower.setter
    def TxPower(self, value: "n"):  # type: ignore
        self._tx_power = value

    @method()
    def Release(self):  # called by bluez when advertisement is being unregistered or cleaned up
        print("[*] Advertisement released by BlueZ")
