import argparse
import json
from replay.utils.common import expand_uuid16
from replay.utils.logger import logger_setup
import argparse
import json
import dbus_next
from dbus_next.aio import MessageBus
import asyncio
from replay.utils.btmgmt_utils import setup_btmgmt
from replay.configs.replay_tool_constants import BLUEZ_SERVICE, ADAPTER_PATH
from replay.utils.adapter_utils import cleanup, set_adapter_alias, register_gatt_hierarchy, register_gatt_application, register_advert
from replay.bluez_gatt.advertisement import Advertisement

logger = logger_setup("replay tool")

CHAR_PARSERS = {
    # [CHAR_UUID16] from JSON Output - Take a JSON Entry and get the values field for each value data
    "0x2a37": lambda e: int(e["values"]["bpm"]),
    "0x2a5f": lambda e: e["values"],
    "0x2b41": lambda e: e["values"]["raw"],
    "0x2b40": lambda e: e["values"]["raw"],
}


def get_char_flags(opcode: str) -> list[str]:
    """Return allowed GATT char flags from ATT Opcode"""
    opcode = opcode.lower()

    if opcode == "0x1b":  # handle value notifcation
        return ["read", "notify"]
    elif opcode in ("0x0a", "0x0b"):  # read request / read response
        return ["read"]
    elif opcode in ("0x12", "0x13"):
        return ["write"]
    else:
        # fall back just to read property
        return ["read"]


def build_service_characteristics_map(data: list):
    """"
    Builds service and characteristics mapping structure from parsed JSON ATT

    Args:
        data (list): Parsed ATT entries loaded from a JSON file.

    Returns:
        tuple[dict, dict]:
            - service_char_map: Mapping of service UUIDs → list of characteristic UUIDs
            - char_values_map: Mapping of characteristic UUIDs → list of parsed values
    """
    service_char_map, char_values_map, char_flags_map = {}, {}, {}

    for e in data:
        service_uuid_128 = expand_uuid16(e.get("service_uuid16"))
        char_uuid_128 = expand_uuid16(e.get("char_uuid16"))
        opcode = e.get("opcode")

        if not service_uuid_128 or not char_uuid_128:
            continue

        # get flags based on opcode
        flags = get_char_flags(opcode)
        char_flags_map[char_uuid_128] = flags

        service_char_map.setdefault(service_uuid_128, [])
        char_values_map.setdefault(char_uuid_128, [])

        # Add characteristic to service
        if char_uuid_128 not in service_char_map[service_uuid_128]:
            service_char_map[service_uuid_128].append(char_uuid_128)

        parser = CHAR_PARSERS.get(e.get("char_uuid16"))
        if parser:
            try:
                value = parser(e)
                char_values_map[char_uuid_128].append(value)
            except (KeyError, TypeError):
                continue

    return service_char_map, char_values_map, char_flags_map

# this time we use dbus to write our peripheral
# we need to implement the org bluez LE Advertisement interface and register it with BlueZ LEAdvertisingManager1 interface

# modern BlueZ (org.bluez.GattService1) does no longer have a Characteristic property listed in its spec
# Instead BlueZ discovers child characteristics automatically by walking the dbus object hierarchy
# doc for basic types in dbus: https://dbus.freedesktop.org/doc/dbus-specification.html#basic-types

# in order to make our peripheral discoverable we need to implement and register and advert object under path/advert0 with a
# org.bluez.LEAdvertisment1


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

    service_char_map, char_values_map, char_flags_map = build_service_characteristics_map(
        data)

    logger.info("Characteristic → Values Map:")
    logger.info(json.dumps(char_values_map, indent=4))

    logger.info(
        "\n-------------------------------------------------------------\n")

    logger.info("Service → Characteristic Map:")
    logger.info(json.dumps(service_char_map, indent=4))

    # connect to bluez system bus
    bus = await MessageBus(bus_type=dbus_next.BusType.SYSTEM).connect()
    node_info = await bus.introspect(BLUEZ_SERVICE, ADAPTER_PATH)

    # get the proxy object so we can get the interface
    proxy = bus.get_proxy_object(BLUEZ_SERVICE, ADAPTER_PATH, node_info)
    await set_adapter_alias(proxy, "FitTrack")

    # export and register all services and characteristics
    path = "/org/replay"
    service_objects = await register_gatt_hierarchy(bus, path, service_char_map, char_values_map, char_flags_map)

    # register application with BlueZ
    await register_gatt_application(proxy, path)

    # create our advert
    advert_path = "/org/replay/advert0"
    advert = Advertisement(advert_path, "FitTrack",
                           list(service_char_map.keys()))

    await register_advert(bus, proxy, advert, advert_path)

    # keep it running
    # keep it running forever (so notify loops stay active)
    try:
        await asyncio.Future()  # this just waits forever until cancelled
    except KeyboardInterrupt:
        print("Stopping GATT server...")
        await cleanup(bus, proxy, advert_path, path)

if __name__ == "__main__":
    asyncio.run(main())
