import asyncio, time
from bluez_peripheral.util import Adapter, get_message_bus, is_bluez_available
from bluez_peripheral.advert import Advertisement
from bluez_peripheral.gatt.service import Service, ServiceCollection
from bluez_peripheral.gatt.characteristic import characteristic, CharacteristicFlags as CF
from bluez_peripheral.agent import YesNoAgent  # for Numeric Comparison (MITM)
from bluez_peripheral.advert import PacketType, AdvertisingIncludes
import dbus_fast
import xml.etree.ElementTree as ET
import xml.dom.minidom

HEARTRATE_SERVICE = "0000180d-0000-1000-8000-00805f9b34fb"
HEARTRATE_MEASUREMENT = "00002a37-0000-1000-8000-00805f9b34fb"
DEVICE_NAME = "Secured Fitness-Tracker Device"
MAX_HEARTRATE_RAMP = 160
MIN_HEARTRATE_RAMP = 60
MAX_HEARTRATE = 250
MIN_HEARTRATE = 70

class HeartRateService(Service):
    def __init__(self):
        super().__init__(HEARTRATE_SERVICE, True)
        self._bpm = MIN_HEARTRATE_RAMP
        self._seq = 0
        self._dir = 1 # ramp direction
        self.ramp_step = 2
        self.manualHR = 0
        self._last = time.time()

    #Secure read to 'trigger pairing' (SC + MITM)
    #simple 8-bit heartrate measurement payload
    @characteristic(HEARTRATE_MEASUREMENT, CF.NOTIFY | CF.READ, CF.ENCRYPT_READ, CF.ENCRYPT_WRITE )
    def heart_rate_measurement(self, opts):
        flags = 0x00
        return bytes([flags, self._bpm & 0xFF])
    
    def notify_hr(self):
        flags = 0x00
        self.heart_rate_measurement.changed(bytes([flags, self._bpm & 0xFF]))

    async def start(self):
        """Tick once per second and send notification if subscribed"""
        while True: 
            if self.manualHR > 0:
                self._bpm = max(MIN_HEARTRATE, min(MAX_HEARTRATE, int(self.manualHR)))
            else: 
                #logic to ramp heartrate up & down 
                self._bpm += self._dir * self.ramp_step
                if self._bpm >= MAX_HEARTRATE_RAMP:
                    self._bpm = MAX_HEARTRATE_RAMP
                    self._dir = -1
                elif self._bpm <= MIN_HEARTRATE_RAMP:
                    self._bpm = MIN_HEARTRATE_RAMP
                    self._dir = +1
            
            #send notification each second
            self.notify_hr()
            await asyncio.sleep(1.0)

"""
Search for a bluetooth adapter that implements org.freedesktop.DBUS.Properties interface on the SYSTEM Bus

Iterates over potential BlueZ adapter object paths, instrospects each one and verifies the presence of org.bluez.Adapter1 interface by  
"""
async def find_adapter_props(bus, max_hci=4, wait_seconds=5):
    deadline = asyncio.get_event_loop().time() + wait_seconds
    while True:
        for i in range(max_hci):
            path = f"/org/bluez/hci{i}"
            try:
                #ask bluez for xml metadata describing all interfaces on the object path --> fails hci does not exist yet
                node = await bus.introspect("org.bluez", path)
                xml_elem = node.to_xml()
                xml_str = ET.tostring(xml_elem, encoding="unicode")
                pretty = xml.dom.minidom.parseString(xml_str).toprettyxml()
                print(pretty)
                # get a proxy object on the path exported on the bus 
                proxy = bus.get_proxy_object("org.bluez", path, node)
                #get an interface exported on this proxy object and connect it to the bus
                #exposes methods to call DBUS methods, listen to signals and get and set properties on interface
                props = proxy.get_interface("org.freedesktop.DBus.Properties")
                # sanity: ensure Adapter1 exists
                try:
                    # get 'Address' or 'Name' as a test read (non-blocking)
                    await props.call_get("org.bluez.Adapter1", "Address")
                except Exception:
                    # If Adapter1 isn't present on this object, skip
                    continue
                return path, props
            except dbus_fast.InterfaceNotFoundError:
                # object exists but properties iface missing; try next
                continue
            except Exception:
                # introspect failed (likely path doesn't exist), just continue
                continue

        if asyncio.get_event_loop().time() > deadline:
            return None, None
        # wait a little and retry if adapter might be coming up
        await asyncio.sleep(0.5)

#for YesNoAgent 
#YesNoAgent(request_confirmation: Callable[[int], Awaitable[bool]], cancel: Callable)
#we need an async function that receives the 6-digit passkey and returns TRUE or FALSE
#we need a function if pairing gets canceled
async def on_request_confirmation(passkey: int) -> bool:
    print(f"[AGENT] Confirm passkey: {passkey:06d} (auto-accepting)")
    return True

async def on_cancel():
    print("[AGENT] Pairing was canceled by the peer")

#In order to set up Adapter alias 
async def set_adapter_alias(bus, name):
    adapter_path, props = await find_adapter_props(bus, max_hci=6, wait_seconds=6)
    if adapter_path is None:
        raise RuntimeError("No BlueZ adapter exposing Properties found on system bus (tried /org/bluez/hci0..hci5).")
    # Set alias
    print(f"Setting Alias on {adapter_path} -> {name}")
    await props.call_set("org.bluez.Adapter1", "Alias", dbus_fast.Variant("s", name))
    return adapter_path

async def main(): 
    #by default message bus is set to system not to session
    bus = await get_message_bus()  

    #check if bluez is available on system bus
    if await is_bluez_available(bus):
        print("BlueZ available on system bus")
    else:
        print("BlueZ not available on system bus")
        return 
    
    agent = YesNoAgent(on_request_confirmation, on_cancel)

    try:
        #register should be set on default in order to accept pairing requests
        await agent.register(bus, default=True)
    except Exception as e:
         print(f"Failed to register agent: {e}")

    service = HeartRateService()

    try: 
        await service.register(bus)
    except Exception as e:
        print(f"Failed to register serivce: {e}")
    
    #set the alias could also be done on console with bluetoothctl
    await set_adapter_alias(bus, DEVICE_NAME)

    advert = Advertisement(
        localName=DEVICE_NAME,
        serviceUUIDs=[HEARTRATE_SERVICE],
        appearance=0,
        timeout=0,
        discoverable=True,
    )

    try:
        await advert.register(bus)
        print("Advertisment registered")
    except Exception as e:
        print(f"Failed to register advertisement: {e}")
    
    print(f"Advertising {DEVICE_NAME} with encrypted services:")
    await asyncio.Event().wait()


if __name__ == "__main__":
    asyncio.run(main())




