# A1 _ BLE Injection
# Attack 2(Corrupted LTK, Paired Device will still connect to attackers BLE Peripheral once LTK is removed or corrupted)

**Goal**
Demonstrate a client-side resumption vulnerability (BLESA class): after a client and device have paired using LE Secure Connections, if the client’s stored bond (LTK) is removed or corrupted, a benign advertiser that advertises the same visible identifiers (name + service UUIDs) can be allowed to reconnect and serve plaintext GATT attribute values without the client enforcing re-pairing or link encryption. The experiment shows that a client/app may accept spoofed data due to incorrect reconnection handling.

ToDo Write a fake client that tries to connect to real peripheral. keys are stored only locally or bond process failed  --> we can try with bleak 

Source: https://www.usenix.org/system/files/woot20-paper-wu.pdf,
"Norec Attack" (CVE-2020–15509) specifically targets BLE implementations using Nordic Semiconductor’s Android libraries
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
