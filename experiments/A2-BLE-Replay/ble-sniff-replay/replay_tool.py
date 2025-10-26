import argparse
import json
import asyncio
import dbus_next
from dbus_next.aio import MessageBus
from dbus_next.service import (
    ServiceInterface, method, dbus_property, PropertyAccess)
from dbus_next import Variant
from common import int_sFloat_le
from utils.btmgmt_utils import setup_btmgmt

# Constants

BLUEZ_SERVICE = "org.bluez"
ADAPTER_PATH = "/org/bluez/hci0"

# this time we use dbus to write our peripheral
# we need to implement the org bluez LE Advertisement interface and register it with BlueZ LEAdvertisingManager1 interface

# modern BlueZ (org.bluez.GattService1) does no longer have a Characteristic property listed in its spec
# Instead BlueZ discovers child characteristics automatically by walking the dbus object hierarchy
# doc for basic types in dbus: https://dbus.freedesktop.org/doc/dbus-specification.html#basic-types

# in order to make our peripheral discoverable we need to implement and register and advert object under path/advert0 with a
# org.bluez.LEAdvertisment1


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


class ReplayCharacteristic(ServiceInterface):
    def __init__(self, path: str, uuid: str, service_path: str, values: list):
        super().__init__("org.bluez.GattCharacteristic1")
        self._path = path
        self._uuid = uuid  # 128 Bit characteristic uuid
        self._service_path = service_path
        self._flags = ["read", "notify"]
        self._values = values
        self._pos = 0
        self._notifying = False
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

    # BlueZ interface has methods: StartNotify(), StopNotify(), Confirm(), ReadValue(), WriteValue()

    @method()
    def ReadValue(self, ops: "a{sv}") -> "ay":  # type: ignore # array of byte
        # guard against out of index
        payload = self.build_payload()
        print(f"→ ReadValue({self._uuid}): {payload.hex()}")

        # why we return list --> python bytes is one scalar types not a list of d-bus byte elements
        # dbus expects a sequence of individual bytes, each being a unsigned 8 bit integer ("y")
        # so we convert through list containing unsigned 8 bit int
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

        # Heartrate Measurement --> integer, 8 bit or 16 bit value
        if isinstance(val, int):
            flags = 0x00
            return bytes([flags, val & 0xFF])

        # Pulse Oximeter Measurement --> dict {bpm, spo2}
        # Pulse Oximeter Continous Measurement and Pulse Oximeter Check Measurement char use the IEEE 11073-20601 SFLOAT
        if isinstance(val, dict):
            flags = 0x00
            bpm = int(val.get("bpm", 0))
            spo2 = int(val.get("spo2", 0))

            payload = bytes([flags]) + int_sFloat_le(spo2) + \
                int_sFloat_le(bpm)
            return payload

        # vendor specific raw hex string
        if isinstance(val, str):
            # TODO test on application fitness tracker
            return bytes.fromhex(val)

        # fallback
        return bytes([0x00])

    async def notify_loop(self):
        while self._notifying:
            val = int(self._values[self._pos % len(self._values)])
            self._pos += 1

            # build the payload mark first byte as flags [0x00] then value
            # format [flags][val]
            payload = self.build_payload()
            # "The cached value of the characteristic. This property gets updated only after a
            # successful read request and when a notification or indication is received, upon
            # which a PropertiesChanged signal will be emitted."
            # emit properties changed

            await self.emit_properties_changed({
                "Value": Variant("ay", payload)
            })

            print(f"→ Notify via PropertiesChanged({self._uuid}): {val}")
            await asyncio.sleep(1.0)


def expand_uuid16(uuid16: str) -> str:
    """Convert 16-bit BLE UUID to full 128-bit UUID."""
    if not uuid16 or not uuid16.startswith("0x"):
        return uuid16
    return f"0000{uuid16[2:]}-0000-1000-8000-00805f9b34fb"


async def main():
    if setup_btmgmt() == False:
        return
    parser = argparse.ArgumentParser(
        description="Replay parsed ATT writes to a BLE device"
    )
    parser.add_argument("att_parsed_output",
                        help="Input parsed attributes of BLE peripheral")
    args = parser.parse_args()

    # Load JSON
    with open(args.att_parsed_output) as f:
        data = json.load(f)

    service_char_map = {}
    char_values_map = {}

    for e in data:
        service_uuid_128 = expand_uuid16(e.get("service_uuid16"))
        char_uuid_128 = expand_uuid16(e.get("char_uuid16"))

        if not service_uuid_128:
            continue

        # Initialize service map
        if service_uuid_128 not in service_char_map:
            service_char_map[service_uuid_128] = []

        # Add characteristic to service
        if char_uuid_128 and char_uuid_128 not in service_char_map[service_uuid_128]:
            service_char_map[service_uuid_128].append(char_uuid_128)

        # Initialize char_values_map
        if char_uuid_128 and char_uuid_128 not in char_values_map:
            char_values_map[char_uuid_128] = []

        # Heart Rate Measurement (0x2A37)
        if char_uuid_128.endswith("2a37-0000-1000-8000-00805f9b34fb"):
            bpm = e.get("values", {}).get("bpm")
            if bpm is not None:
                char_values_map[char_uuid_128].append(int(bpm))

        # Pulse Oximeter Measurement (0x2A5F)
        elif char_uuid_128.endswith("2a5f-0000-1000-8000-00805f9b34fb"):
            values = e.get("values")
            if values:
                char_values_map[char_uuid_128].append(values)

        # Physical Activity (0x2B41)
        elif char_uuid_128.endswith("2b41-0000-1000-8000-00805f9b34fb"):
            raw = e.get("values", {}).get("raw")
            if raw:
                char_values_map[char_uuid_128].append(raw)

        # Sleep Data (0x2B40)
        elif char_uuid_128.endswith("2b40-0000-1000-8000-00805f9b34fb"):
            raw = e.get("values", {}).get("raw")
            if raw:
                char_values_map[char_uuid_128].append(raw)

    # Pretty print results
    print("Characteristic → Values Map:")
    print(json.dumps(char_values_map, indent=4))

    print("\n-------------------------------------------------------------\n")

    print("Service → Characteristic Map:")
    print(json.dumps(service_char_map, indent=4))

    # connect to bluez system bus
    bus = await MessageBus(bus_type=dbus_next.BusType.SYSTEM).connect()

    # Get the GattManager

    node_info = await bus.introspect(BLUEZ_SERVICE, ADAPTER_PATH)

    # get the proxy object so we can get the interface
    proxy = bus.get_proxy_object(BLUEZ_SERVICE, ADAPTER_PATH, node_info)

    adapter_props = proxy.get_interface("org.freedesktop.DBus.Properties")
    # set alias name
    await adapter_props.call_set("org.bluez.Adapter1", "Alias", Variant("s", "Replay"))

    # get the interface so we can call methods
    # source for methods: https://git.kernel.org/pub/scm/bluetooth/bluez.git/tree/doc/org.bluez.GattManager.rst
    gatt_props = proxy.get_interface("org.bluez.GattManager1")

    # export and register all services and characteristics
    path = "/org/replay"
    service_objects = []

    for i, (service_uuid, characteristics) in enumerate(service_char_map.items()):
        # create GattService
        # define service path --> e.g. /org/replay/service1
        service_path = f"{path}/service{i}"
        service = GATTService(service_path, service_uuid, True)

        # export service interface on bluez system bus
        bus.export(service_path, service)

        service_objects.append(service)

        for j, (char_uuid_128) in enumerate(characteristics):
            # define characteristic path --> e.g. org/replay/service1/char1
            char_path = f"{service_path}/char{j}"
            values = char_values_map.get(char_uuid_128, [0])
            characteristic = ReplayCharacteristic(
                char_path, char_uuid_128, service_path, values)

            # export characteristic interface on bluez system bus
            bus.export(char_path, characteristic)

            print(i, char_uuid_128, char_values_map.get(char_uuid_128, [0]))

    # register application with BlueZ
    await gatt_props.call_register_application(path, {})
    print("✅ GATT Replay Application Registered with BlueZ")

    # after registering we need to create our advertisement object
    advert_path = "/org/replay/advert0"
    advert = Advertisement(advert_path, "Replay",
                           list(service_char_map.keys()))
    bus.export(advert_path, advert)

    # register advert on LeAdvertisingManager1
    le_advert_manager_1 = proxy.get_interface(
        "org.bluez.LEAdvertisingManager1")
    await le_advert_manager_1.call_register_advertisement(advert_path, {})
    print("✅ Advertisement registered with BlueZ")

    # keep it running
    try:
        await asyncio.Future()
    except KeyboardInterrupt:
        print("Stopping GATT server...")


if __name__ == "__main__":
    asyncio.run(main())
