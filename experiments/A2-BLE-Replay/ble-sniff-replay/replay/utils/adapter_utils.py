from replay.bluez_gatt.gatt_service import GATTService
from replay.bluez_gatt.gatt_characteristic import ReplayCharacteristic
from replay.bluez_gatt.advertisement import Advertisement
from dbus_next import Variant
from dbus_next.aio import MessageBus
from dbus_next.aio.proxy_object import ProxyObject
from replay.utils.logger import logger_setup
logger = logger_setup(__name__)


async def set_adapter_alias(proxy_object: ProxyObject, peripheral_name: str):
    """
    Set Bluetooth adapter alias

    :param proxy_object: Proxy object for the BlueZ adapter (from MessageBus.introspect)
    :param peripheral_name: Name to set for adapter alias
    """
    try:
        adapter_props = proxy_object.get_interface(
            "org.freedesktop.DBus.Properties")

        await adapter_props.call_set("org.bluez.Adapter1",
                                     "Alias", Variant("s", peripheral_name))

        logger.info(
            f"Setting Alias on {adapter_props.path} -> {peripheral_name}")
    except Exception:
        logger.error(
            f"Failed to set Alias on {adapter_props.path} with name {peripheral_name}")


async def register_gatt_hierarchy(bus: MessageBus, base_path: str, service_char_map: dict, char_values_map: dict, char_flags_map: dict):
    """
    Create and register GATT services and characteristics on BlueZ system bus

    Args:
        bus: Active D-Bus connection
        base_path: Root object path (e.g., "/org/replay")
        service_char_map: Dict mapping service UUIDs → list of characteristic UUIDs
        char_values_map: Dict mapping characteristic UUIDs → list of values
    """
    service_objects = []

    for i, (service_uuid, characteristics) in enumerate(service_char_map.items()):
        # define service path --> e.g. /org/replay/service0
        service_path = f"{base_path}/service{i}"

        # create GattService
        service = GATTService(service_path, service_uuid, True)

        # export service interface on bluez system bus
        bus.export(service_path, service)
        service_objects.append(service)

        # register characteristics for this service
        for j, (char_uuid_128) in enumerate(characteristics):
            # define characteristic path --> e.g. org/replay/service1/char0
            char_path = f"{service_path}/char{j}"
            values = char_values_map.get(char_uuid_128, [0])
            flags = char_flags_map.get(char_uuid_128, [0])
            characteristic = ReplayCharacteristic(
                char_path, char_uuid_128, service_path, values, flags)

            # export characteristic interface on bluez system bus
            bus.export(char_path, characteristic)

    return service_objects


async def register_gatt_application(proxy_object: ProxyObject, path: str):
    try:
        # get the interface so we can call methods
        # source for methods: https://git.kernel.org/pub/scm/bluetooth/bluez.git/tree/doc/org.bluez.GattManager.rst
        gatt_props = proxy_object.get_interface("org.bluez.GattManager1")

        await gatt_props.call_register_application(path, {})
        logger.info("GATT Replay Application registered with BlueZ")
    except Exception:
        logger.error(
            "Failed at registering GATT Replay Application with BlueZ")


async def register_advert(bus: MessageBus, proxy_object: ProxyObject, advert: Advertisement, advert_path: str):
    try:
        # export system interface on bluez system bus
        bus.export(advert_path, advert)

        # register Advertisement on LeAdvertisingManager1
        le_advert_manager_1 = proxy_object.get_interface(
            "org.bluez.LEAdvertisingManager1")

        await le_advert_manager_1.call_register_advertisement(advert_path, {})
        logger.info("Advertisement registered with BlueZ")

    except Exception:
        logger.error(
            "Failed at registering Advertisement with BlueZ")


async def cleanup(bus: MessageBus, proxy: ProxyObject, advert_path: str, app_path: str):
    """Unregister GATT application and advertisement before shutdown."""
    # Unregister advertisement
    try:
        le_adv_mgr = proxy.get_interface("org.bluez.LEAdvertisingManager1")
        await le_adv_mgr.call_unregister_advertisement(advert_path)
        logger.info("Unregister advertisement from BlueZ")
    except Exception as e:
        logger.warning(f"Failed to unregister advertisement: {e}")

    # Unregister GATT application
    try:
        gatt_mgr = proxy.get_interface("org.bluez.GattManager1")
        await gatt_mgr.call_unregister_application(app_path)
        logger.info("Unregistere GATT application from BlueZ")
    except Exception as e:
        logger.warning(f"Failed to unregister GATT application: {e}")

    await bus.disconnect()
