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
- App scans on device name or service uuids for subscribing to GATT characteristics

**Procedure**
- Real BLE Peripheral advertises
- Attacker wants to know the UUIds for the Service and Characteristic in order to do that a **bluetoothctl scan on** will be done
- Attacker gets bunch of MAC Addresses from devices --> Pinpoints target through RSSI Proximity when the name is not clear (in our case name is very clear)
- Attacker advertises fake BLE Periperal

**Success**
- App connect to the Peripheral by scanning for the Service uuids
- App subcribes to the characteristic of the fake BLE device
- App receives tampered payloads
- Tampered payloads will be fowarded to Backend

**Metrics**
- Number of spoofed health data received from fake ble device
- Number of spoofed health data fowarded to backend

**How to run the program**
sudo node index.js --name "HeartRate" --service "180d" --char "2a37"
