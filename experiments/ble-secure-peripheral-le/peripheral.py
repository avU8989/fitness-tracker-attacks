
from utils.adapter_utils import set_adapter_alias, cleanup, register_advert, register_gatt_application, register_agent
from utils.btmgmt_utils import setup_btmgmt
import dbus_next
from dbus_next.aio import MessageBus
import asyncio
import traceback
from asyncio import Queue, Event, create_task
import logging
from bluez_gatt.services.physical_activity_monitor_service import PhysicalActivityMonitorService
from bluez_gatt.services.sleep_monitor_service import SleepMonitorService
from bluez_gatt.services.pulse_oximeter_service import PulseOximeterService
from bluez_gatt.services.heart_rate_service import HeartRateService
from bluez_gatt.characteristics.heart_rate_meas_char import HeartMeasurementCharacteristic
from bluez_gatt.characteristics.physical_activity_meas_char import StepCounterCharacteristic
from bluez_gatt.characteristics.pulse_oximeter_meas_char import PulseOximeterMeasurementCharacteristic
from bluez_gatt.characteristics.sleep_activity_meas_char import SleepMeasurementCharacteristic
from bluez_gatt.advertisement import Advertisement
from bluez_gatt.gatt_agent import Agent

BLUEZ_SERVICE = "org.bluez"
ADAPTER_PATH = "/org/bluez/hci1"
AGENT_PATH = "/org/bluez/ble_secure_peripheral_le_sc_agent"

# STANDARD UUIDS BY BLUETOOTH (SIG)
HEARTRATE_SERVICE = "0000180d-0000-1000-8000-00805f9b34fb"
HEARTRATE_MEASUREMENT = "00002a37-0000-1000-8000-00805f9b34fb"
PULSEOXIMETER_SERVICE = "00001822-0000-1000-8000-00805f9b34fb"
PLX_CONT_MEAS = "00002a5f-0000-1000-8000-00805f9b34fb"
PHYSICAL_ACTIVITY_SERVICE = "0000183E-0000-1000-8000-00805f9b34fb"
STEP_COUNTER_MEASUREMENT = "00002b40-0000-1000-8000-00805f9b34fb"
SLEEP_MONITOR_SERVICE = "00001111-0000-1000-8000-00805f9b34fb"
SLEEP_MEASUREMENT = "00002b41-0000-1000-8000-00805f9b34fb"

DEVICE_NAME = "FitTrack"
GREEN = "\033[92m"
RESET = "\033[0m"
YELLOW = "\033[93m"
RED = "\033[91m"

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger(__name__)


async def queue_control_consumer(service: PhysicalActivityMonitorService | SleepMonitorService, queue: Queue, stop_event: Event):
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
            # Real Peripheral Command (RPMCD)
            line = await loop.run_in_executor(None, input, f"{GREEN}[RPMCD]{RESET} ")
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
            print("Real Peripheral Commands:")
            print(
                "  pams <...>       send command to Physical Activity Monitor Service")
            print(
                "  sams <...>       send command to Sleep Activity Monitor Service")
            print("  exit")
            print("  help")
            continue

        if head == "exit":
            # we need to notify others to clean up and stop
            print(f"{YELLOW}RPCMD exiting...")
            print(f"{YELLOW}Stopping services...")
            print(f"{GREEN}Stopped RPCMD")

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
                await sams_queue.join()
            except asyncio.CancelledError:
                break

        print("Unknown target. Prefix commands with 'pams' or 'sams'. Type 'help'.")


async def main():
    bus = await MessageBus(bus_type=dbus_next.BusType.SYSTEM).connect()
    try:
        node_info = await bus.introspect(BLUEZ_SERVICE, ADAPTER_PATH)

        # get the proxy object
        proxy = bus.get_proxy_object(BLUEZ_SERVICE, ADAPTER_PATH, node_info)

        await set_adapter_alias(proxy, DEVICE_NAME)

        # create the agent
        agent = Agent()
        await register_agent(bus, agent, AGENT_PATH, capability="DisplayYesNo")

        path = "/org/ble_secure_peripheral_le_sc"
        heartrate_service_path = f"{path}/heartrate_service"
        physical_activity_service_path = f"{path}/physical_activtity_service"
        pulse_oximeter_service_path = f"{path}/pulse_oximeter_service"
        sleep_service_path = f"{path}/sleep_activity_service"

        heartrate_meas_char_path = f"{heartrate_service_path}/heart_measurement"
        step_counter_char_path = f"{physical_activity_service_path}/step_counter"
        pulse_oximeter_meas_char_path = f"{pulse_oximeter_service_path}/pulse_oximeter_measurement"
        sleep_meas_char_path = f"{sleep_service_path}/sleep_monitor_measurement"

        # ------------------------Create GATT Characteristics-------------------------------

        # we are anticipating that the client pairs first in order to read our encrypted characteristics
        # bluez checks link security level --> if not encrypted/authenticated start pairing process, pairing will therefore trigger agent
        # to pair we need to add an agent from org.bluez.Agent with a passkey implementation
        # after pairing suceeds the link becomes encrypted and authenticated

        # Bluetooth LE Security Level 3 --> Encrypt + Authenticated (MITM protected)

        heartrate_meas_char = HeartMeasurementCharacteristic(
            heartrate_meas_char_path, HEARTRATE_MEASUREMENT, heartrate_service_path, ["read", "encrypt-authenticated-read", "notify", "encrypt-authenticated-notify"])

        step_counter_char = StepCounterCharacteristic(
            step_counter_char_path, STEP_COUNTER_MEASUREMENT, physical_activity_service_path, [
                "read", "encrypt-authenticated-read", "notify", "encrypt-authenticated-notify"]
        )

        pulse_oximeter_meas_char = PulseOximeterMeasurementCharacteristic(
            pulse_oximeter_meas_char_path, PLX_CONT_MEAS, pulse_oximeter_service_path, ["read", "encrypt-authenticated-read"])

        sleep_meas_char = SleepMeasurementCharacteristic(
            sleep_meas_char_path, SLEEP_MEASUREMENT, sleep_service_path, [
                "read", "encrypt-authenticated-read", "notify", "encrypt-authenticated-notify"]
        )
        # ------------------------Create GATT Services-------------------------------

        heartrate_service = HeartRateService(
            heartrate_service_path, HEARTRATE_SERVICE, heartrate_meas_char)

        physical_activity_service = PhysicalActivityMonitorService(
            physical_activity_service_path, PHYSICAL_ACTIVITY_SERVICE, step_counter_char
        )

        pulse_oximeter_service = PulseOximeterService(
            pulse_oximeter_service_path, PULSEOXIMETER_SERVICE, pulse_oximeter_meas_char
        )

        sleep_activity_service = SleepMonitorService(
            sleep_service_path, SLEEP_MONITOR_SERVICE, sleep_meas_char)

        # ------------------------Export Service on Bluez System Bus------------

        bus.export(heartrate_service_path, heartrate_service)
        bus.export(physical_activity_service_path,
                   physical_activity_service)
        bus.export(pulse_oximeter_service_path,
                   pulse_oximeter_service)
        bus.export(sleep_service_path, sleep_activity_service)

        # ------------------------Export Characteristics on Bluez System Bus------------

        bus.export(heartrate_meas_char_path, heartrate_meas_char)
        bus.export(step_counter_char_path, step_counter_char)
        bus.export(pulse_oximeter_meas_char_path, pulse_oximeter_meas_char)
        bus.export(sleep_meas_char_path, sleep_meas_char)

        await register_gatt_application(proxy, path)

        service_uuids = [HEARTRATE_SERVICE,
                         PHYSICAL_ACTIVITY_SERVICE, PULSEOXIMETER_SERVICE, SLEEP_MONITOR_SERVICE]

        advert_path = f"{path}/advert0"
        advert = Advertisement(advert_path, DEVICE_NAME, service_uuids)

        try:
            await register_advert(bus, proxy, advert, advert_path)
            print(
                f"{GREEN}-------------------Real Peripheral with LE started---------------")

            print(
                f"-------------------Advertisment registered-----------------------{RESET}")
        except Exception as e:
            print(f"Failed to register advertisement: {e}")

        # create queues & stop event
        pams_queue = Queue()  # Physical Activity Monitor Service
        sams_queue = Queue()  # Sleep Activity Monitor Service
        stop_event = Event()

        tasks = [asyncio.create_task(queue_control_consumer(
            physical_activity_service, pams_queue, stop_event)), asyncio.create_task(queue_control_consumer(sleep_activity_service, sams_queue, stop_event))]

    except Exception:
        print("Top-level exception while setting up:")
        traceback.print_exc()

    try:
        wait_task = [asyncio.create_task(
            bus.wait_for_disconnect()), asyncio.create_task(stop_event.wait()), asyncio.create_task(stdin_reader_and_dispatch(
                pams_queue, sams_queue, stop_event))]

        # clean shutdown, we wait until BlueZ disconnects or stop_event is set
        done, pending = await asyncio.wait(wait_task, return_when=asyncio.FIRST_COMPLETED)

        for t in pending:
            t.cancel()
    finally:
        stop_event.set()
        await cleanup(bus, proxy, advert_path, path)

        for t in tasks:
            t.cancel()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Exiting")
