# A2 - BLE Replay

## Goal ## 
The attacker who can retrieve a phone's `btsnoop_hci.log` can fully reconstruct the phone's ATT/GATT activity. By **parsing ATT records** (READ, WRITE, NOTIFY) through the **opcodes** the attacker **extracts the service and characteristic UUIDs** and learns the payload structure used by the app/real peripheral. With this data they can generate a **fake BLE peripheral** (advertising the same Service UUIDS, exposing the same characterstics and returning matching payload values). This lets an adversary trick the app into trusting a malicious device, enabling **data replay** and **spoofed readings**.

The App will scan the device based on **name** and **uuids**, even though **BLE Protocol for Security (LE Secure Connection, RPA)** is **correctly implemented**, once paired with the real peripheral the attacker can spoof the **MAC and name of the device**, so **fake ble peripheral** will be connected to app **even though a bond for the real peripheral was created**. 

## Threat Model Mapping — STRIDE

| STRIDE Category | Entry Point(s) | Description | Potential Impact |  Mitigations |
|-----------------|----------------|--------------|------------------|------------------------|
| **Spoofing** | • BLE Advertising <br> • GATT Characteristics <br> • App connection logic| Attacker impersonates the real peripheral and streams fake health data|• Data integrity compromise • Falsified health records, Incorrect Analysis for health metrics|**LE Secure Connection** with **MITM protection** (Numerical Response) and a additional **Challenge Response Protocol** (CRP) verifying Identity|
| **Repudiation** |• Client (App) & Server (Peripheral) communication|App cannot prove who sent the reading | • No proof that streamed health data came from genuine tracker <br> • Loss of accountability| Implement a **digital-signature based CRP** (ECDH/ECDSA) to verify peripheral → **App authentication layer**
| **Information Disclosure** |• HCI snoop log <br> • Unencrypted GATT read/notify traffic|Attacker extracts health values, UUIDS and ATT from captured hci snoop log traffic|• Privacy leakage (heartrate, spo2, sleep acitivity, steps counter) <br>• Easier reverse engineering due to unencrypted characteristics| Use encrypted characteristics (**encrypt-authenticated-***) 
| **Tampering** |• BLE payload capture |Data could be altered after capture|• Falsified health records|**LE SC + Numerical Passkey (MITM) + CRP**
|**Elevation of Privilege**|• App connection logic|Inadequate connection logic|•App trusts only upon correct device name or/and matching UUIDs <br> • Rogue tracker gains unauthorized access to sensitive health metrics| Restrict Reads to bonded & trusted clients → **LE SC + MITM + Numerical Passkey (MITM) + CRP**

## Precondition ## 
- **Host-side Linux environment configured with `bluetoothctl agent` and `btmgmt` flags for LE Secure Connections and pairing**

- The "fitness-tracker" App will connect automatically connect to devices based on visible identifiers **(Device Name, Advertised UUIDs)**

- The "fitness-tracker" App does not require pairing or encryption

- The legitimate peripheral exposes **unencrypted GATT characteristics** and transmits **plaintext payload values**

- The legitimate peripheral may be **offline (e.g. powered off)** or **turned on too late**

- Bluetooth for both adapters are not soft blocked (hci0, hci1) and both are running 

- Developer settings and HCI snoop logging are enabled on the smartphone, so btsnoop_hci.log captures the phone’s HCI traffic and is available to an attacker with ADB/root/physical access.

- Bluetoothd is set with experimental flags

## Procedure ## 
| Step | Description |
|------|-------------|
| **1. Pairing & Normal Scenario** | The real peripheral is paired with the mobile app and the app performs reads and subscribes to notifications for health metrics. |
| **2. Capture** | The phone's HCI snoop log (`btsnoop_hci.log`) records the ATT/GATT exchange (Read Request, Read Response, Notifcation handles, etc.). |
| **3. Snoop Log Extraction** | The attacker obtains the phone's snoop log (via ADB, bugreport or physical acccess). |
|**4. Parse ATT/GATT**|The attacker parses the snoop log and extracts ATT events and metadata - service UUIDs, characterstic UUIDs, opcodes (0x1b (notify), 0x0a (read request), 0x0b (read-response)), handles and payload bytes structure|
|**5. Infer payload formats**|From observation, attacker reverse engineers the payload and records these mappings into a model (JSON)|
|**6. Advertise as target**|With that model, the attacker implements a BLE peripheral that exposes same service UUIDs, characteristic UUIDs and payload formats. The fake peripheral will serve read-responses and notifcations matching the observed formats. The attacker advertises the fake peripheral using same visible identifier (device name/ UUID) as the legitimate peripheral. |
|**7. Exploitation of Timing / Availability**|Legitimate peripheral is offline or is not available in time. The app scans and discovers the attacker's fake peripheral first.|
|**8. App Connection Logic & Receiving Data**|App connects & consumes data: The app (which connects based on device name/UUID) connects to fake peripheral, issues reads/subscribes to notifcation and receives replayed telemetry|
|**9. Backend ingestion** |Replayed data will be forwarded to backend, which treats it as authentic data from original device (peripheral)|


## Captured Data ##
 - To-Do add logging to attacker peripheral and secure peripheral

## Success Criteria ## 
	≥ 95% of replayed health data will appear in backend

## Mitigation Under Test

### 🔹 BLE Link Layer:
- **LE Secure Connection**
- **RPA** (Resolvable Private Address) for real BLE peripheral
- **Pairing / Bonding** using numerical passkey and `DisplayYesNo` agent
- **Challenge–Response Protocol** with **digital signature with Eliptic Curve (ECDSA-P256)**
---
### 🔹 App Layer:
- Store bond metadata using **`react-native-keychain`**
- Implement connection logic that verifies peripheral identity via **challenge–response** using **digital signatures**
- Store the **public key** of the digital signature received from the BLE peripheral

## Metrics ## 
	acceptance rate of replayed values

## How to run the Attack ##


## Notes / Safety ##
https://dl.acm.org/doi/10.1145/3548606.3559372 --> Vulnerability in RPA, using RPA still vulnerable to replay attacks

This should contain a lightweight HCI sniffer an ATT write parser (btsnoop-based), and a replay utility to resend parsed ATT/GATT to target device

Phone needs to be set on Developer Settings --> tap build number 7 times
In Developer Settings you have to enable Bluetooth HCI snoop log 

step 1: fetch the bluetooth hci snoop log 
step 2: load into pcap wireshark
step 3: parse gatt att from wireshark pcap 
step 4: attacker knows which services are used and which characteristics respond to which values
step 5: attacker sends exactly same payloads again

hci is the interface between the bluetooth stack of the android system and the bluetooth chip on the phone 

# needs Wireshark 4.4 or newer
sudo add-apt-repository ppa:wireshark-dev/stable -y
sudo apt update
sudo apt install wireshark

sudo apt install tshark

pip install pyshark


#Notes
This will pop up in the bluetoothd experimental logs, when the peripheral has set bondable properties but doesnt provide a numerical passkey or numeric confirmation
```bash
bluetoothd[35422]: src/adapter.c:bonding_attempt_complete() hci0 bdaddr BC:93:07:DF:C7:57 type 1 status 0x5
bluetoothd[35422]: src/device.c:device_bonding_complete() bonding (nil) status 0x05
bluetoothd[35422]: src/device.c:device_bonding_failed() status 5
bluetoothd[35422]: src/adapter.c:resume_discovery() 
bluetoothd[35422]: src/shared/mgmt.c:can_read_data() [0x0000] command 0x001d complete: 0x00
bluetoothd[35422]: src/shared/mgmt.c:can_read_data() [0x0000] event 0x000c
bluetoothd[35422]: src/adapter.c:dev_disconnected() Device BC:93:07:DF:C7:57 disconnected, reason 3
bluetoothd[35422]: src/adapter.c:adapter_remove_connection() 
bluetoothd[35422]: plugins/policy.c:disconnect_cb() reason 3

```
avu@avu-Lenovo-V15-G4-ABP:~/fitness-tracker-attacks/experiments/A2-BLE-Replay/ble-sniff-replay$ busctl introspect org.bluez /org/bluez/hci0

