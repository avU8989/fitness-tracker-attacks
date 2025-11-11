from dbus_next.service import (
    ServiceInterface, method, dbus_property, PropertyAccess)
import asyncio
import traceback
from dbus_next import DBusError


class GATTCharacteristicBase(ServiceInterface):
    def __init__(self, path: str, uuid: str, service_path: str, flags: list[str], value: bytes = b"\x00"):
        super().__init__("org.bluez.GattCharacteristic1")
        self._path = path
        self._uuid = uuid  # 128 Bit characteristic uuid
        self._service_path = service_path
        self._gatt_flags = flags
        self._value = value

        self._notifying: bool = False
        self._notifying_task = None

    @dbus_property(access=PropertyAccess.READ)  # read only on doc
    def UUID(self) -> "s":  # string  # type: ignore
        return self._uuid

    @dbus_property(access=PropertyAccess.READ)  # read only on doc
    # according to doc must be a syntactically valid object path  # type: ignore
    def Service(self) -> "o":  # type: ignore
        return self._service_path

    @dbus_property(access=PropertyAccess.READ)  # read only on doc
    def Flags(self) -> "as":  # array of string  # type: ignore
        return self._gatt_flags

    # "Starts a notification session from this characteristic if it supports value
    # notifications or indications" from the doc
    @dbus_property(access=PropertyAccess.READ)
    def Value(self) -> "ay":  # array of byte
        return self._value

    @dbus_property(access=PropertyAccess.READ)
    def Notifying(self) -> "b":
        return self._notifying

    @method()
    def WriteValue(self, value: "ay", opts: "a{sv}"):  # type: ignore
        # convert
        data = bytes(value)
        if not any("write" in flag for flag in self._gatt_flags):
            print(f"[!] WriteValue called but not supported on {self._uuid}")
            raise DBusError(
                "org.bluez.Error.NotSupported",
                "WriteValue not supported for this characteristic"
            )

        self._value = data

        # if a subclass has on_write() --> call it
        if hasattr(self, "on_write"):
            try:
                self.on_write(data, opts)
            except Exception as e:
                print(f"[!] Error during writing value for {self._uuid}")
                traceback.print_exc()
                raise DBusError("org.bluez.Error.Failed", str(e))
        return

    @method()
    def ReadValue(self, opts: "a{sv}") -> "ay":  # type: ignore # array of
        if not any(flag.endswith("read") for flag in self._gatt_flags) and "read" not in self._gatt_flags:
            print(f"[!] ReadValue called but not supported on {self._uuid}")
            raise DBusError(
                "org.bluez.Error.NotSupported",
                "ReadValue not supported for this characteristic"
            )

        # if a sublcass has on_read() --> call it
        try:
            if hasattr(self, "on_read"):
                return getattr(self, "on_read")(opts)
        except Exception as e:
            traceback.print_exc()
            raise DBusError(
                "org.bluez.Error.Failed",
                e
            )

        return self._value

    @method()
    def StartNotify(self):
        if any(flag.endswith("notify") for flag in self._gatt_flags):
            # start notifying
            self._notifying = True
            self._notifying_task = asyncio.create_task(self.notify_loop())
        else:
            print(f"Characteristic does not support Notify Requests")

    @method()
    def StopNotify(self):
        if self._notifying:
            # stop notify
            self._notifying = False
            if self._notifying_task:
                self._notifying_task.cancel()
        else:
            print(f"[!] StopNotify called but was not notifying {self._uuid}")

    async def notify_loop(self):
        while self._notifying:
            try:

                # emit properties changed wants python type not dbus type --> dbus next already does the converting
                # was an error in my previous implementation
                self.emit_properties_changed({
                    "Value": self._value,
                    "Notifying": True
                })

            except Exception as e:
                print(f"[notify_loop ERROR for {self._uuid}]: {e}")
                traceback.print_exc()
            await asyncio.sleep(1.0)
