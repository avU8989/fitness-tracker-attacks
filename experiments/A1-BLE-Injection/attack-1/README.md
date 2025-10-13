# A1 _ BLE Injection
# Attack 1(Just Works Pairing / Legacy Pairing)

**Goal**
Prove that a spoofed BLE peripheral advertising the same service/characteristics UUIDs as a real device can trick an app into connecting, subscribing and
forwarding tampered health data to the backend **when LE Secure Connections is not in use (legacy pairing / Just Works)

**Threats**
- App connects to attacker peripheral and subcribes to GATT characteristics
- App forwards spoofed/tampered health data to backend

**Precondition**
- No LE Secure Connections on the peripheral (devices uses legacy pairing, Just Works or does not require pairing/encryption)
- ("Real Smartwatch" in our case Real Peripheral) is powererd on when Attacker scans for Service and Characteristics identifiers as well as the MAC Address of the real peripheral
- After Attackers scanning scenario where real ble peripheral is turned off
- App scans on device name or service uuids for subscribing to GATT characteristics

**Procedure**
- Real BLE Peripheral advertises
- Attacker wants to know the UUIds for the Service and Characteristic in order to do that a **bluetoothctl scan on** will be done
- Attacker gets bunch of MAC Addresses from devices --> Pinpoints target through RSSI Proximity when the name is not clear (in our case name is very clear)
- User turns off real BLE Peripheral (Real Smartwatch)
- Attacker advertises fake BLE Periperal

**Success**
- App connect to the Peripheral by scanning for the Service uuids
- App subcribes to the characteristic of the fake BLE device
- App receives tampered payloads
- Tampered payloads will be fowarded to Backend

**Metrics**
- Number of spoofed health data received from fake ble device
- Number of spoofed health data fowarded to backend

**Mitigation run (version 1)**
we need BLE Security, if the characteristics require encryption and authentication notifications, app won't subcribe --> spoofing blocked

require encryption on GATT characteristic --> by adding CF.ENCRYPTED...

on the host side: 
pairing method (MITM vs Just Works), bonding, LE Secure Connection --> set via bluetoothctl agent (or in our code through YesNoAgent) and btmgmt flags


**How to run the program**
sudo node index.js --name "Secured Fi" --service "180d" --char "2a37"
