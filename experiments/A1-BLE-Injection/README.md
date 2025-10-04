# A1 _ BLE Injection (Unbonded Characteristic)

**Goal**

**Threats**

**Precondition**
Not encrypted UUIds for both Service and Characteristics

**Procedure**
Attacker wants to know the UUIds for the Service and Characteristic. Does a bluetoothctl scan on. Gets bunch of MAC Addresses from devices? 
How can he pinpoint the target and pull the Service/Characteristics UUIDs using the BlueZ tools. :
	- Proximity (RSSI): the closest device usually has higher RSSI (less negative)scan 

so do a bluetooth scan --> scan for mac addresses
meanwhile do a btmon scan look for advertiser service uuids and char uuids --> you can actually see a lot there
**Success**

**Mitigation run*

**Metrics**

**How to run the program**
sudo node index.js --name "HeartRate" --service "180d" --char "2a37"
