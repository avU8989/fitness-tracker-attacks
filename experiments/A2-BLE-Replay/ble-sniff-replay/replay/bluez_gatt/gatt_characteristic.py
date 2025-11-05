from dbus_next.service import (
    ServiceInterface, method, dbus_property, PropertyAccess)
import asyncio
from replay.utils.common import int_sFloat_le
import traceback

# https://git.kernel.org/pub/scm/bluetooth/bluez.git/tree/doc


class ReplayCharacteristic(ServiceInterface):
    def __init__(self, path: str, uuid: str, service_path: str, values: list, flags: list):
        super().__init__("org.bluez.GattCharacteristic1")
        self._path = path
        self._uuid = uuid  # 128 Bit characteristic uuid
        self._service_path = service_path
        self._flags = flags
        self._values = values
        self._value = b"\x00"  # place holder for cached char value
        self._pos = 0
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
        return self._flags

    # "Starts a notification session from this characteristic if it supports value
    # notifications or indications" from the doc
    @dbus_property(access=PropertyAccess.READ)
    def Value(self) -> "ay":  # array of byte
        return self._value

    @dbus_property(access=PropertyAccess.READ)
    def Notifying(self) -> "b":
        return self._notifying

    # BlueZ interface has methods: StartNotify(), StopNotify(), Confirm(), ReadValue(), WriteValue()

    @method()
    def ReadValue(self, ops: "a{sv}") -> "ay":  # type: ignore # array of byte
        # guard against out of index
        payload = self.build_payload()
        print(f"→ ReadValue({self._uuid}): {payload.hex()}")

        return payload

    @method()
    def StartNotify(self):
        if not self._notifying:
            # start notifying
            print(f"[+] StartNotify({self._uuid})")
            self._notifying = True
            self._notifying_task = asyncio.create_task(self.notify_loop())
        else:
            print(f"[+] Already notifying...")

    @method()
    def StopNotify(self):
        if self._notifying:
            # stop notify
            print(f"[-] StopNotify({self._uuid})")
            self._notifying = False
            if self._notifying_task:
                self._notifying_task.cancel()
        else:
            print(f"[!] StopNotify called but was not notifying {self._uuid}")

    def build_payload(self) -> bytes:
        """Convert current value to bytes depending on format"""
        val = self._values[self._pos % len(self._values)]
        self._pos += 1

        # heartrate measurement --> integer, 8 bit or 16 bit value
        if isinstance(val, int):
            flags = 0x00
            return bytes([flags, val & 0xFF])

        # pulse oximeter measurement --> dict {bpm, spo2}
        # pulse oximeter continous measurement and pulse oximeter check measurement char use the IEEE 11073-20601 SFLOAT
        if isinstance(val, dict):
            flags = 0x00
            bpm = int(val.get("bpm", 0))
            spo2 = int(val.get("spo2", 0))

            payload = bytes([flags]) + int_sFloat_le(spo2) + \
                int_sFloat_le(bpm)
            return payload

        # vendor specific raw hex string
        if isinstance(val, str):
            return bytes.fromhex(val)

        # fallback
        return bytes([0x00])

    async def notify_loop(self):
        print(f"[notify_loop] started for {self._uuid}")
        while self._notifying:
            try:
                payload = self.build_payload()
                self._value = payload

                # emit properties changed wants python type not dbus type --> dbus next already does the converting
                # was an error in my previous implementation
                self.emit_properties_changed({
                    "Value": payload,
                    "Notifying": True
                })

                print(
                    f"→ Notify via PropertiesChanged({self._uuid}): {payload.hex()}")
            except Exception as e:
                print(f"[notify_loop ERROR for {self._uuid}]: {e}")
                traceback.print_exc()
            await asyncio.sleep(1.0)
