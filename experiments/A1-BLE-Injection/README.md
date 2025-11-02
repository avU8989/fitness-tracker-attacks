# A1 _ BLE Injection
### Attack 1 - App-layer trust failure over secured BLE
We assume that the attacker knows the GATT services and characteristics UUIDs and can discover the device's advertised name. By advertising a **fake BLE peripheral** that matches those visible identifiers, an attacker can cause the **fitness-tracker app to** connect because the app’s connection logic trusts the device name alone. Even when the real peripheral uses privacy (**RPA**), **bonding**, and **LE Secure Connections**, those link protections do not guarantee the peer’s identity — the application layer must still authenticate and validate all device messages.

### Attack 2 - Corrputed/removed bonding state (bonding misconfiguration)
The second issue would arise from mismanaged or corrupted bonding state (LTKs, IRKs).Research papers have shown that upon removed or corrupted bonding states, an attacker can advertise a peripheral exposing unencrypted or unauthenticated characteristics that the app may accept. 

Source: https://www.usenix.org/system/files/woot20-paper-wu.pdf,

# Hardware Environment #
The attack scenario has been conducted on : 
- **Client Device**: Samsung Galaxy S24+ with One UI 6.1 — running the fitness tracker app
- **Unhardened (legitimate) peripheral**: Honor 8 - running the peripheral on nrF Connect
- **Attacker peripheral**: Linux host running BlueZ (**hci1**), using Bluetooth Toggle to present the spoofing peripheral.
- **Hardened (real) peripheral (hosted)**: Linux host running BlueZ (**hci0**) using my laptop’s Bluetooth adapter.

### Linux Host (Peripheral Environment Details)
| Component              | Details                                                                                                                                                                                         |
| ---------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **OS**                 | Ubuntu 24.04.3 LTS (Noble)                                                                                                                                                                      |
| **Kernel**             | 6.14.0-1014-oem x86_64                                                                                                                                                                          |
| **BlueZ Version**      | 5.72                                                                                                                                                                                            |
| **Adapter (hci0)**     | Realtek Semiconductor Corp. (Manufacturer ID 93)                                                                                                                                                |
| **HCI Version**        | 5.1 (Revision: 0xcc6, Subversion: 0xd2e3)                                                                                                                                                       |
| **Adapter Name**       | `FitTrack`                                                                                                                                                           

## Project Structure ##
The peripherals **(real / attacker)** will follow the almost the same project structure.

The project structure for the **attacker peripheral**: 
``` bash
├── attacker_peripheral.py # the main file in order to run the peripheral
├── common.py # constants (service uuids) and parsers
├── services # GATT Services with their characteristics
│   ├── fake_heart_rate_service.py
│   ├── fake_physical_activity_monitor_service.py
│   ├── fake_pulse_oximeter_service.py
│   └── fake_sleep_monitor_service.py
└── utils
    ├── adapter_utils.py # hci adapter utils 
    └── btmgmt_utils.py # script for running btmgmt commands
```

The project structure for the **hardened peripheral**: 
```bash
├── common.py
├── README.md
├── secured_fitness_tracker_peripheral.py # the main file 
├── services
│   ├── heart_rate_service.py
│   ├── physical_activtiy_service.py
│   ├── pulse_oximeter_service.py
│   ├── secure_service.py # challenge response service with EC encryption
│   └── sleep_monitor_service.py
└── utils
    ├── adapter_utils.py # hci adapter utils 
    └── btmgmt_utils.py # script for running btmgmt commands
```

## Installment & Setup Environment ##
The **A1 - BLE Injection** will use:
- **bluez-peripheral** - a python library for setting up a GATT peripheral. 
- **dbus-fast** - a python library for communicating with the D-Bus message bus.

To install run: 
``` bash
# Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate   # On Windows: venv\Scripts\activate

# Install the library
pip install bluez-peripheral
pip install dbus-fast
```
- **BlueZ** - the official Linux Bluetooth stack that provides core Bluetooth utilities and daemons. It should be installed and running on your host system. 
Install it using your systems packet manager (on most Linux dist):

``` bash
sudo apt update
sudo apt install bluez bluez-tools
```
This installs `bluetoothd`, `btmgmt` and related CLI tools.
- **bluetoothd** the main Bluetooth daemon included with BlueZ. Make sure it is enabled and running with experimental flags to support advanced BLE features.

```bash 
sudo /usr/libexec/bluetooth/bluetoothd --experimental --noplugin=a2dp,avrcp,media,input,network,mcp,tmap,vcp,aics,vocs,mics,bap,bass,has,csip -n -d #load only gatt
```

⚠️ **Note**: Before running this command, ensure that no other instance of bluetoothd is already active, as multiple daemons can interfere with BLE peripheral behavior. If needed, you can mask the default system service to prevent it from starting automatically:
``` bash
sudo systemctl stop bluetooth
sudo systemctl mask bluetooth
```
- **HCI interfaces** (`hci0`, `hci1`, etc) - represent physical or virtual Bluetooth adapters. You can check your bluetooth adapters with: 
``` bash
hciconfig -a
```
⚠️ **Note**: Make sure the bluetooth adapters are not **softblocked**
``` bash
rfkill list
```
If e.g. **hci0 is down or softblocked**, run the following commands: 
``` bash
sudo hciconfig hci0 up
rsudo rfkill unblock bluetooth
```
- **btmgmt** - a command-line tool from BlueZ suite used to configure Bluetooth controllers and enable bluetooth features. The peripheral setup scripts will execute `btmgmt`commands to manage adapter states and enable required bluetooth features during testing. 

First you need to setup your adapters to match the experiment
I have two hci adapters hci0 is my attacker and hci1 is my real one

If you want to run the secure peripheral (real one), then you have to set your adapters correctly, unfortunately it is hardcoded in my project to hci1, so unless you change that 

The hci1 runs on a bluetooth toggle and the secure peripheral doesnt set up the btmgmt settings via a script, you have to do it explicity by accessing the btmgmt command line tool

there we set out settinngs

power off

bredr off

le on

advertising on

sc on 

discov yes

after that you can run the periheral script more info on the readmes in each attack/hardened peripheral folder


## Setup App ##
The **main branch contains** the **unhardened app** - follow the same instruction steps for the **hardened build** but switch to the **security branch** to run the protected version.

- clone original fitness-tracker app repo [https://github.com/avU8989/fitness_tracker](https://github.com/avU8989/fitness_tracker)

- in the frontend directory do a `npm install` as the frontend will not be dockerized
- Both the frontend and backend use environment files — create a `.env` in the root of the `frontend/` directory and another `.env` in the root of the `backend/` directory.
-  ### .env File for Frontend:
```ini
# API endpoint to the backend (you can use ngrok or localhost)
API_URL=  https://"your-ngrok-url"" 
```
-  ### .env File for Backend: 
```ini
#JWT Secret Key
JWT_SECRET=yourSuperSecretKeyHere

# MongoDB connection string
MONGODB_URI=mongodb://root:example@mongodb:27017/fitness_tracker?authSource=admin

# Path to the OpenAPI spec
OPEN_API_DESIGN=./fitness_tracker.yaml
```
- `docker compose up -d` will create one container **fitness_tracker** with two image files for **Backend API** and **MongoDB Database**

- to run the **React Native App**, run the following command `npx expo start -c`, then press **"a"** to launch it on Android. Ensure your phone is connected and recognized as an **ADB device** beforehand. For that you must set your phone on **developer mode**.
