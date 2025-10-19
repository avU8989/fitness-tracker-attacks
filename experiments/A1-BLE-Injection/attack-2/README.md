# A1 - BLE Injection 
# Attack 2 (Unprotected App Layer, Protected BLE Layer - Enforced LE Secure Connection, Encrypted/Authenticated Write/Read Requests) #

## Goal ## 

The App will scan the device based on **name** and **uuids**, even though **BLE Protocol for Security** is **correctly implemented**, once paired the attacker can spoof the **MAC and name of the device**, **fake ble peripheral** will be connected to app **even though a bond was created**. 

## Threat Model Mapping — STRIDE

| STRIDE Category | Entry Point(s) | Description | Potential Impact |  Mitigations |
|-----------------|----------------|--------------|------------------|------------------------|
| **Spoofing / Tampering** | • BLE advertising<br>• GATT characteristics<br>• App pairing & connect logic<br>• App → Backend HTTPS transfer | Adversary impersonates a peripheral sending tampered data to the app. | • Data integrity compromise<br>• Incorrect application behavior<br>• Safety / compliance risks | • Enforce authenticated pairing<br>• Use challenge–response protocol<br>• Verify peripheral identity with digital signatures<br>• Avoid trusting on Device name / MAC alone |


## Setup (Original app) ##


- clone original fitness-tracker app repo [https://github.com/avU8989/fitness_tracker](https://github.com/avU8989/fitness_tracker)

- frontend dir and backend dir do a `npm install`
- the frontend and backend both use .env files so you need to create them 
- ### .env File for App: ###
```ini
# API endpoint to the backend (you can use ngrok or localhost)
API_URL=  https://"your-ngrok-url"" 
```
- ### .env File for Backend: ###
```ini
#JWT Secret Key
JWT_SECRET=yourSuperSecretKeyHere

# MongoDB connection string
MONGODB_URI=mongodb://admin:admin123@mongo:27017/fitness_tracker?authSource=admin

# Path to the OpenAPI spec
OPEN_API_DESIGN=./fitness_tracker.yaml
```
- `docker compose up -d` will create one container **fitness_tracker** with two image files for **Backend API** and **MongoDB Database**

## Precondition ## 
- **Host-side Linux environment configured with `bluetoothctl agent` and `btmgmt` flags for LE Secure Connections and pairing**

- The "fitness-tracker" App will connect automatically connect to devices based on visible identifiers **(Device Name, Advertised UUIDs)**

- The legitimate peripheral may be **offline (e.g. powered off)** or **turned on too late**

## Procedure ## 
**1.** **Real peripheral is paired to app**

**2.**  **Attacker does a bluetoothctl scan on his device --> (shows device name of real peripheral, static mac address of real peripheral and uuids )**

**3.** **Attacker clones mac/device name of real peripheral and advertises his fake peripheral**

**4.** **Real peripheral is turned off (no battery or so) or turned on too late**

**5.** **Attacker spoofs ble peripheral and advertises fake ble peripheral**

**6.** **App sees device name "Secure FitTracker" and connnects upon device name or mac address**

**7.** **Attacker injects tampered health data to app**

**8.** **Tampered data will be forwarded to backend**


## Captured Data ##
 - To-Do add logging to attacker peripheral and secure peripheral

## Success Criteria ## 
	≥ 95% of forged health data will appear in backend

## Mitigation Under Test

### 🔹 BLE Link Layer:
- **LE Secure Connection**
- **RPA** (Resolvable Private Address) for real BLE peripheral
- **Pairing / Bonding** using numerical passkey and `YesNoAgent`
- **Challenge–Response Protocol** with **digital signature with Eliptic Curve (ECDSA-P256)**
---
### 🔹 App Layer:
- Store bond metadata using **`react-native-keychain`**
- Implement connection logic that verifies peripheral identity via **challenge–response** using **digital signatures**
- Store the **public key** of the digital signature received from the BLE peripheral

## Metrics ## 
	acceptance rate of forged values

## Setup Secure Version of App ##
	-To-Do

## Setup Secure Version of Secure BLE Peripheral ##


## How to run the Attack ##
### Step 1 - Check Bluetooth adapter status ###
First we want to check if the hciconfig for bluetooth is softblocked or not

```bash
sudo rfkill list 
```
---
### Step 2 — Unblock adapter (if needed) ###
If the hci Bluetooth is `Soft blocked: yes`, unblock by running the command:

```bash 
sudo rfkill unblock bluetooth
```
---
### Step 3 — Verify no Bluetooth daemon is running ###

Ensure that no Bluetooth daemon is currently active by running the following command:

```bash 
ps aux | grep [b]luetoothd # list bluetoothd processes
```
---

### Step 4 — Start the Bluetooth daemon (experimental mode) ###

Launch the Bluetooth daemon in experimental mode using the following command: 

```bash 
sudo /usr/libexec/bluetooth/bluetoothd --experimental --noplugin=a2dp,avrcp,media,input,network -n -d # load only GATT
```
---

### Step 5 — Run the peripheral script ###

Run the peripheral script to advertise the fake BLE device:

```bash 
python3 attacker_peripheral.py
```
---


## Notes / Safety ##
### Setup Notes: ###
By default, the bluetoothd daemon on Linux does not enable the experimental D-Bus interfaces (GattManager1, LEAdvertisingManager1, etc.).
Without these, user-space programs (like scripts using **bluez_peripheral**) can advertise but cannot accept GATT connections — clients (phones, nRF Connect, etc.) will see the device but fail to connect.

**Start bluetoothd with experimental flags** (will enable experimental features, and should only load GATT)

### Attack Procedure Notes: ###
Attacker wants to know the UUIds for the Service and Characteristic. Does a bluetoothctl scan on. Gets bunch of MAC Addresses from devices? 

How can he pinpoint the target and pull the Service/Characteristics UUIDs using the **BlueZ tools** :
- Proximity (RSSI): the closest device usually has higher RSSI (less negative)scan 
- Name like Secure FitTracker: attacker can guess that this is our real peripheral name and scans for service uuids

Attacker can guess Services and Characteristics just by inspecting the app (HeartRate, Sleep, Physical Activity Monitor and Pulse Oximeter)

### How to run Attacker Peripheral Notes: ###
**Note:** btmgmt is used to initialize the adapter — the peripheral script invokes the following commands
```bash
	sudo btmgmt power off
	sudo btmgmt bredr off
	sudo btmgmt le on
	sudo btmgmt connectable on
	sudo btmgmt advertising on
	sudo btmgmt bondable on
	sudo btmgmt discov yes
	sudo btmgmt power on
```