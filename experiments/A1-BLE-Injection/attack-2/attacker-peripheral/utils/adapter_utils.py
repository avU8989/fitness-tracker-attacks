import asyncio
import dbus_fast
import logging
# https://dbus-fast.readthedocs.io/en/latest/

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger(__name__)


async def find_adapter_props(bus, wait_seconds=5):
    """Return (path, props) for the first BlueZ adapter visible on D-Bus."""

    deadline = asyncio.get_event_loop().time() + wait_seconds
    while True:
        try:
            # introspect the root /org/bluez to see available hci nodes
            root = await bus.introspect("org.bluez", "/org/bluez")
            for node in root.nodes:
                if node.name.startswith("hci"):
                    path = f"/org/bluez/{node.name}"
                    try:
                        # introspect the data for the node
                        node_info = await bus.introspect("org.bluez", path)

                        # we get the proxy object and it should export the interfaces and the nodes specified in the introspected data
                        proxy = bus.get_proxy_object(
                            "org.bluez", path, node_info)

                        # we want to get the proxy interface so we can call methods in order to call the DBus methods, get properties and set properties
                        # here we want to obtain the org.freedesktiop.DBus.Properties interface so we can get/set BlueZ properties
                        props = proxy.get_interface(
                            "org.freedesktop.DBus.Properties")

                        addr = await props.call_get("org.bluez.Adapter1", "Address")
                        logger.info(
                            f"Found adapter {path} (Address: {addr.value})")
                        return path, props
                    except Exception as e:
                        print(f"Skipping {path}: {e}")
                        continue
        except Exception as e:
            logger.error(f"Could not introspect /org/bluez: {e}")

        if asyncio.get_event_loop().time() > deadline:
            logger.error("Timeout waiting for adapter")
            return None, None

        await asyncio.sleep(0.5)


async def set_adapter_alias(bus, name):
    """Find the active Adapter and set its Alias property"""

    adapter_path, props = await find_adapter_props(bus)
    if adapter_path is None:
        raise RuntimeError(
            "No BlueZ adapter exposing Properties found on system bus (tried /org/bluez/hci0..hci5).")

    # Use properties interface to call set method to update the Adapter1.Alias field
    # D-Bus value is here a string with the signature "s"
    logger.info(f"Setting Alias on {adapter_path} -> {name}")
    await props.call_set("org.bluez.Adapter1", "Alias", dbus_fast.Variant("s", name))
    return adapter_path
