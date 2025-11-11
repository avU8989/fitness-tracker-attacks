
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
from bluez_gatt.characteristics.health_sensor.heart_rate_meas_char import HeartMeasurementCharacteristic
from bluez_gatt.characteristics.health_sensor.physical_activity_meas_char import StepCounterCharacteristic
from bluez_gatt.characteristics.health_sensor.pulse_oximeter_meas_char import PulseOximeterMeasurementCharacteristic
from bluez_gatt.characteristics.health_sensor.sleep_activity_meas_char import SleepMeasurementCharacteristic
from bluez_gatt.characteristics.challenge_response.challenge_write_char import ChallengeCharacteristic
from bluez_gatt.characteristics.challenge_response.signature_read_char import SignatureCharacteristic
from bluez_gatt.characteristics.challenge_response.public_key_read_char import PublicKeyCharacteristic
from bluez_gatt.services.secure_service import SecureService
from bluez_gatt.advertisement import Advertisement
from bluez_gatt.gatt_agent import Agent
import utils.common as common

BLUEZ_SERVICE = "org.bluez"
ADAPTER_PATH = "/org/bluez/hci1"
AGENT_PATH = "/org/bluez/ble_secure_peripheral_le_sc_agent"

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

    # store the public key persistently, because previously every time we restart the peripheral
    # a new key is being generated and the app cant keep up with the update,
    # because it stores and reads the old keypair so it wont know that the peripheral generated a new keypair

    bus = await MessageBus(bus_type=dbus_next.BusType.SYSTEM).connect()
    try:
        node_info = await bus.introspect(BLUEZ_SERVICE, ADAPTER_PATH)

        # get the proxy object
        proxy = bus.get_proxy_object(BLUEZ_SERVICE, ADAPTER_PATH, node_info)

        await set_adapter_alias(proxy, DEVICE_NAME)

        # create the agent
        agent = Agent()
        await register_agent(bus, agent, AGENT_PATH, capability="DisplayYesNo")

        path = "/org/ble_secure_peripheral_le_sc_crp"
        heartrate_service_path = f"{path}/heartrate_service"
        physical_activity_service_path = f"{path}/physical_activtity_service"
        pulse_oximeter_service_path = f"{path}/pulse_oximeter_service"
        sleep_service_path = f"{path}/sleep_activity_service"
        secure_service_path = f"{path}/crp_service"

        heartrate_meas_char_path = f"{heartrate_service_path}/heart_measurement"
        step_counter_char_path = f"{physical_activity_service_path}/step_counter"
        pulse_oximeter_meas_char_path = f"{pulse_oximeter_service_path}/pulse_oximeter_measurement"
        sleep_meas_char_path = f"{sleep_service_path}/sleep_monitor_measurement"
        challenge_write_char_path = f"{secure_service_path}/challenge"
        signature_read_char_path = f"{secure_service_path}/signature"
        public_key_char_path = f"{secure_service_path}/public_key"

        # ------------------------Create GATT Characteristics-------------------------------

        # we are anticipating that the client pairs first in order to read our encrypted characteristics
        # bluez checks link security level --> if not encrypted/authenticated start pairing process, pairing will therefore trigger agent
        # to pair we need to add an agent from org.bluez.Agent with a passkey implementation
        # after pairing suceeds the link becomes encrypted and authenticated

        # *************************Health Sensor Characteristics*****************************
        # in our previous ble secure peripheral version, we enabled le sc (on the controllers side [hci adapter bluetooth])
        # but encrypt-authenticated read/write characateristics on the peripheral,
        # there is still a possibility that the attacker downgrades to legacy pairing,if their device does not support Le Secure Connection,
        # thus we need to ensure that our peripheral only accepts LE Secure Connections with the flags "secure *", accepting only LE SC Connection

        # as the doc says the secure flags are only available for the server side

        # Bluetooth LE Security Level 4 --> Secure Notify/Read/Write --> client must use LE SC link only

        heartrate_meas_char = HeartMeasurementCharacteristic(
            heartrate_meas_char_path, common.HEARTRATE_MEASUREMENT, heartrate_service_path, ["read", "secure-read", "notify", "secure-notify"])

        step_counter_char = StepCounterCharacteristic(
            step_counter_char_path, common.STEP_COUNTER_MEASUREMENT, physical_activity_service_path, ["read",
                                                                                                      "secure-read", "notify", "secure-notify"]
        )

        pulse_oximeter_meas_char = PulseOximeterMeasurementCharacteristic(
            pulse_oximeter_meas_char_path, common.PLX_CONT_MEAS, pulse_oximeter_service_path, ["read", "secure-read"])

        sleep_meas_char = SleepMeasurementCharacteristic(
            sleep_meas_char_path, common.SLEEP_MEASUREMENT, sleep_service_path, [
                "read", "secure-read", "notify", "secure-notify"]
        )

        # -----------------Create CRP Service with Digital Signature-----------------
        secure_service = SecureService(
            secure_service_path, common.SECURE_SERVICE, True)

        # ****************Challenge Response Protocol Characteristics****************

        challenge_char = ChallengeCharacteristic(
            challenge_write_char_path, common.CHALLENGE_CHAR, secure_service, ["write", "secure-write"])

        signature_char = SignatureCharacteristic(
            signature_read_char_path, common.SIGN_CHAR, secure_service, ["read", "secure-read"])

        public_key_char = PublicKeyCharacteristic(
            public_key_char_path, common.PUBLIC_KEY_CHAR, secure_service, ["read", "secure-read"])

        # ------------------------Create GATT Services-------------------------------

        heartrate_service = HeartRateService(
            heartrate_service_path, common.HEARTRATE_SERVICE, heartrate_meas_char)

        physical_activity_service = PhysicalActivityMonitorService(
            physical_activity_service_path, common.PHYSICAL_ACTIVITY_SERVICE, step_counter_char
        )

        pulse_oximeter_service = PulseOximeterService(
            pulse_oximeter_service_path, common.PULSEOXIMETER_SERVICE, pulse_oximeter_meas_char
        )

        sleep_activity_service = SleepMonitorService(
            sleep_service_path, common.SLEEP_MONITOR_SERVICE, sleep_meas_char)

        # ------------------------Export Service on Bluez System Bus------------

        bus.export(heartrate_service_path, heartrate_service)
        bus.export(physical_activity_service_path,
                   physical_activity_service)
        bus.export(pulse_oximeter_service_path,
                   pulse_oximeter_service)
        bus.export(sleep_service_path, sleep_activity_service)
        bus.export(secure_service_path, secure_service)

        # ------------------------Export Characteristics on Bluez System Bus------------

        bus.export(heartrate_meas_char_path, heartrate_meas_char)
        bus.export(step_counter_char_path, step_counter_char)
        bus.export(pulse_oximeter_meas_char_path, pulse_oximeter_meas_char)
        bus.export(sleep_meas_char_path, sleep_meas_char)
        bus.export(challenge_write_char_path, challenge_char)
        bus.export(signature_read_char_path, signature_char)
        bus.export(public_key_char_path, public_key_char)

        await register_gatt_application(proxy, path)

        service_uuids = [common.HEARTRATE_SERVICE,
                         common.PHYSICAL_ACTIVITY_SERVICE, common.PULSEOXIMETER_SERVICE, common.SLEEP_MONITOR_SERVICE, common.SECURE_SERVICE]

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
