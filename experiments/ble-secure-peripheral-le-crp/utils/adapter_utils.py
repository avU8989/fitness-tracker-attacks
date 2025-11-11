import asyncio
from dbus_next import Variant
from dbus_next.aio import MessageBus
from dbus_next.aio.proxy_object import ProxyObject
import logging
# https://dbus-fast.readthedocs.io/en/latest/
import dbus_fast
from dbus_next.aio.proxy_object import ProxyObject
from bluez_gatt.advertisement import Advertisement
from bluez_gatt.gatt_agent import Agent
import traceback
logger = logging.getLogger(__name__)


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


async def register_gatt_application(proxy_object: ProxyObject, path: str):
    """Registering GATT application"""
    try:
        # get the interface so we can call methods
        # source for methods: https://git.kernel.org/pub/scm/bluetooth/bluez.git/tree/doc/org.bluez.GattManager.rst
        gatt_props = proxy_object.get_interface("org.bluez.GattManager1")

        await gatt_props.call_register_application(path, {})
        logger.info("GATT Replay Application registered with BlueZ")
    except Exception:
        logger.error(
            "Failed at registering GATT Replay Application with BlueZ")


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

    bus.disconnect()


async def register_advert(bus: MessageBus, proxy_object: ProxyObject, advert: Advertisement, advert_path: str):
    """Register a custom Bluetooth LE Advertisement with BlueZ

        :param bus: D-Bus system/session bus
        :param proxy_object: Bluez proxy object in order to get interface
        :param advert: Your custom Advertisement implementing the ServiceInterface org.bluez.LEAdvertisement1
        :param advert_path: The D-Bus object path where the advertisement is exported
    """
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


async def register_agent(bus: MessageBus, agent: Agent, agent_path: str, capability="DisplayYesNo"):
    """Register a custom Bluetooth Agent with BlueZ

        :param bus: D-Bus system/session bus
        :param proxy_object: BlueZ proxy object in order to get the interface
        :param agent: Your custom Agent implementing the ServiceInterface of org.bluez.Agent
        :param advert_path: The D-Bus object path where the agent is exported
    """
    try:
        # export system interface on bluez system bus
        bus.export(agent_path, agent)

        # introspect the bluez root
        node_info = await bus.introspect("org.bluez", "/org/bluez")
        bluez_root_proxy = bus.get_proxy_object(
            "org.bluez", "/org/bluez", node_info)

        agent_manager = bluez_root_proxy.get_interface(
            "org.bluez.AgentManager1")

        # register Agent on AgentManager1
        #
        await agent_manager.call_register_agent(agent_path, capability)
        logger.info("Agent registered with BlueZ")
        # set Agent to default
        await agent_manager.call_request_default_agent(agent_path)
        logger.info("Agent registered with BlueZ")
    except Exception:
        traceback.print_exc()

        logger.error(
            f"Failed at registern Agent with capability: {capability}")
