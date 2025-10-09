# A1 _ BLE Injection (Unbonded Characteristic)

**Goal**

**Threats**

**Precondition**
Not encrypted UUIds for both Service and Characteristics

Hostside linux environment for bluetooth ctl agent and btmgmt flags --> LE Secure Connection, pairing method

Logging enabled on app layer, backend layer and ble peripheral 

By default, the bluetoothd daemon on Linux does not enable the experimental D-Bus interfaces (GattManager1, LEAdvertisingManager1, etc.).
Without these, user-space programs (like scripts using bluez_peripheral) can advertise but cannot accept GATT connections — clients (phones, nRF Connect, etc.) will see the device but fail to connect.

**Procedure**
Attacker wants to know the UUIds for the Service and Characteristic. Does a bluetoothctl scan on. Gets bunch of MAC Addresses from devices? 
How can he pinpoint the target and pull the Service/Characteristics UUIDs using the BlueZ tools. :
	- Proximity (RSSI): the closest device usually has higher RSSI (less negative)scan 

so do a bluetooth scan --> scan for mac addresses
meanwhile do a btmon scan look for advertiser service uuids and char uuids --> you can actually see a lot there

(1)attacker advertises fake ble peripheral 
(2)"real" hardeneded smartwatch will also be advertised at the same time with encrypted characteristics
(3)host side enforce LE Secure Connections + MITM + bonding
    host setup: 
    sudo btmgmt -i hci0 power off
    sudo btmgmt -i hci0 le on
    sudo btmgmt -i hci0 bredr off
    sudo btmgmt -i hci0 privacy on
    sudo btmgmt -i hci0 power on

    sudo bluetoothctl
    agent DisplayYesNo
    default-agent
    pariable on

procedure: 
    - first subcribe attempt --> pairing prompt appears on phone
    - bluetoothctl infro <MAC> shows Paired: yes, Bonded: yes
    - btmon shows encrypted link after pariing
    - unbonded fake wont be able to deliver notifications that the app acecepts, app only complete the subscription on bonded, encrypted link
**Success**

**Mitigation run (version 1)**
we need BLE Security, if the characteristics require encryption and authentication notifications, app won't subcribe --> spoofing blocked

require encryption on GATT characteristic --> by adding secure: ['notify','read','write']

on the host side: 
pairing method (MITM vs Just Works), bonding, LE Secure Connection --> set via bluetoothctl agent and btmgmt flags

on the app layer: 
retry subscription after the OS shows the pariing UI and finishes
only auto connect/subscribe to bonded device ID you learned the first time

**Metrics**

**How to run the program**
sudo node index.js --name "HeartRate" --service "180d" --char "2a37"

Steps to run: 
Run these commands in order:
sudo pkill bluetoothd
sudo rfkill unblock bluetooth
sudo modprobe -r btusb
sleep 2
sudo modprobe btusb
sleep 4


ps aux | grep [b]luetoothd --> output should be nothing

Start bluetoothd with experimental flags
sudo /usr/libexec/bluetooth/bluetoothd --experimental -n -d

We’ll use btmgmt to set up the adapter cleanly.
sudo btmgmt power off
sudo btmgmt bredr off
sudo btmgmt le on
sudo btmgmt connectable on
sudo btmgmt advertising on
sudo btmgmt bondable on
sudo btmgmt power on

verify with 
sudo btmgmt info
you should see : current settings: powered connectable bondable le advertising secure-conn

run the peripheral with: python3 peripheral.py

Documentation: 
https://dbus-fast.readthedocs.io/en/latest/message-bus/base-message-bus.html
https://bluez-peripheral.readthedocs.io/en/latest/index.html