# A1 _ BLE Injection (Unbonded Characteristic)

**Goal**
Tampered Data will be forwarded to backend and spoofed ble peripheral will act as fake ble device of attacker

**Threats**
Tampered Data will be accepted on backend side
App will connect to attackers ble peripheral, app will subscribe to attackers gatt service and characteristic, attackers ble peripheral will notify app

**Precondition**
Not encrypted UUIds for both Service and Characteristics
Real Smartwatch has to be turned off 

**Procedure**
Attacker wants to know the UUIds for the Service and Characteristic. Does a bluetoothctl scan on. Gets bunch of MAC Addresses from devices? 
How can he pinpoint the target and pull the Service/Characteristics UUIDs using the BlueZ tools. :
	- Proximity (RSSI): the closest device usually has higher RSSI (less negative)scan 

so do a bluetooth scan --> scan for mac addresses
meanwhile do a btmon scan look for advertiser service uuids and char uuids --> you can actually see a lot there

attacker advertises fake ble peripheral --> connects to app --> app receives tampered payloads --> app sends these payloads to backend

**Success**


**Metrics**

**How to run the program**
sudo node index.js --name "HeartRate" --service "180d" --char "2a37"
