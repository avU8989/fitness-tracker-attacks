import asyncio
from asyncio import Queue, Event, create_task
from bluez_peripheral.util import Adapter, get_message_bus, is_bluez_available
from bluez_peripheral.advert import Advertisement
from bluez_peripheral.gatt.service import Service, ServiceCollection
from bluez_peripheral.gatt.characteristic import characteristic, CharacteristicFlags as CF
from bluez_peripheral.agent import YesNoAgent  # for Numeric Comparison (MITM)
from bluez_peripheral.advert import PacketType, AdvertisingIncludes
from services.heart_rate_service import HeartRateService, HEARTRATE_SERVICE
from services.physical_activtiy_service import PHYSICAL_ACTIVITY_SERVICE, PhysicalActivityMonitorService
from services.pulse_oximeter_service import PulseOximeterService, PULSEOXIMETER_SERVICE
from services.sleep_monitor_service import SleepMonitorService, SLEEP_MONITOR_SERVICE
from services.secure_service import SecuredService, SECURE_SERVICE

from utils.adapter_utils import set_adapter_alias, set_adapter_discoverable, set_adapter_powered
from utils.btmgmt_utils import setup_btmgmt


DEVICE_NAME = "Secured FitTrack"
GREEN = "\033[92m"
RESET = "\033[0m"
YELLOW = "\033[93m"


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
            # Real Peripheral Command (APCMD)
            line = await loop.run_in_executor(None, input, f"{GREEN}[RPCMD]{RESET} ")
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
                await pams_queue.join()
            except asyncio.CancelledError:
                break

        print("Unknown target. Prefix commands with 'pams' or 'sams'. Type 'help'.")


async def on_request_confirmation(passkey: int) -> bool:
    print(f"[AGENT] Confirm passkey: {passkey:06d} (auto-accepting)")
    return True


async def on_cancel():
    print("[AGENT] Pairing was canceled by the peer")


async def main():
    if (setup_btmgmt() == False):
        return

    # by default message bus is set to system not to session
    bus = await get_message_bus()

    # check if bluez is available on system bus
    if await is_bluez_available(bus):
        print("BlueZ available on system bus")
    else:
        print("BlueZ not available on system bus")
        return

    # for YesNoAgent
    # YesNoAgent(request_confirmation: Callable[[int], Awaitable[bool]], cancel: Callable)
    # we need an async function that receives the 6-digit passkey and returns TRUE or FALSE
    # we need a function if pairing gets canceled
    # guard against MITM attacks
    agent = YesNoAgent(on_request_confirmation, on_cancel)

    try:
        # register should be set on default in order to accept pairing requests
        await agent.register(bus, default=True)
    except Exception as e:
        print(f"Failed to register agent: {e}")

        # create the services

    heartrate_service = HeartRateService()
    pulse_oximeter_service = PulseOximeterService()
    physical_activity_service = PhysicalActivityMonitorService()
    sleep_monitor_service = SleepMonitorService()
    secured_service = SecuredService()

    try:
        services = ServiceCollection()
        services.add_service(secured_service)
        services.add_service(heartrate_service)
        services.add_service(pulse_oximeter_service)
        services.add_service(physical_activity_service)
        services.add_service(sleep_monitor_service)
        await services.register(bus)
    except Exception as e:
        print(f"Failed to register serivce: {e}")

    # set the alias could also be done on console with bluetoothctl
    await set_adapter_alias(bus, DEVICE_NAME)

    advert = Advertisement(
        localName=DEVICE_NAME,
        serviceUUIDs=[HEARTRATE_SERVICE,
                      PULSEOXIMETER_SERVICE,
                      PHYSICAL_ACTIVITY_SERVICE,
                      SLEEP_MONITOR_SERVICE,
                      SECURE_SERVICE],
        appearance=0,
        timeout=0,
        discoverable=True,
        includes=AdvertisingIncludes.TX_POWER,
        duration=65535
    )

    try:
        await advert.register(bus)
        print("-------------------Advertisment registered-----------------------")
    except Exception as e:
        print(f"Failed to register advertisement: {e}")

    # create queues & stop event
    pams_queue = Queue()  # Physical Activity Monitor Service
    sams_queue = Queue()  # Sleep Activity Monitor Service
    stop_event = Event()

    tasks = [
        asyncio.create_task(heartrate_service.start()),
        asyncio.create_task(queue_control_consumer(
            physical_activity_service, pams_queue, stop_event)),
        asyncio.create_task(queue_control_consumer(
            sleep_monitor_service, sams_queue, stop_event)),
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
