sudo sh -c 'btmon -w pcaps/btmon_capture.pcap 2>&1 | tee pcaps/btmon_capture.log' & echo $! > .btmon_pid
echo "btmon started, pid in .btmon_pid"

sudo kill $(cat .btmon_pid) && rm -f .btmon_pid
echo "btmon stopped"


https://dl.acm.org/doi/10.1145/3548606.3559372 --> Vulnerability in RPA, using RPA still vulnerable to replay attacks

This should contain a lightweight HCI sniffer an ATT write parser (btsnoop-based), and a replay utility to resend parsed ATT/GATT to target device

Phone needs to be set on Developer Settings --> tap build number 7 times
In Developer Settings you have to enable Bluetooth HCI snoop log 

step 1: fetch the bluetooth hci snoop log 
step 2: load into pcap wireshark
step 3: parse gatt att from wireshark pcap 
step 4: replay attack 

hci is the interface between the bluetooth stack of the android system and the bluetooth chip on the phone 

# problem
after capturing the hci snoop log upon inspecting the pcap file, on my device there will be one handle identifiers (0x002a) mapped to the two different Service UUIDS 
0x002a --> mapped to Generic Media Control : Media Player Name
0x002a --> mapped to Heart Rate : Heart Rate Measurement

# needs Wireshark 4.4 or newer
sudo add-apt-repository ppa:wireshark-dev/stable -y
sudo apt update
sudo apt install wireshark

sudo apt install tshark

pip install pyshark

GATT mapping from my pcap 
Handle  UUID                              UUID Name
0x0001  1801                              GATT
0x0002  2803                              Characteristic
0x0003  2a05                              Service Changed
0x0004  2803                              Characteristic
0x0005  2b3a                              Server Supported Features
0x0006  2803                              Characteristic
0x0007  2b29                              Client Supported Features
0x0008  2803                              Characteristic
0x0009  2b2a                              Database Hash
0x0014  1800                              GAP
0x0015  2803                              Characteristic
0x0016  2a00                              Device Name
0x0017  2803                              Characteristic
0x0018  2a01                              Appearance
0x0019  2803                              Characteristic
0x001a  2aa6                              Central Address Resolution
0x0028  180d                              Heart Rate
0x0029  2803                              Characteristic
0x002a  2a37                              Heart Rate Measurement
0x002a  2b93                              Media Player Name
0x002a  2b93                              Media Player Name
0x002a  2b93                              Media Player Name
0x002a  2b93                              Media Player Name
0x002b  2902                              Client Characteristic Configuration
0x002c  2803                              Characteristic
0x002d  2a38                              Body Sensor Location
0x002d  2b96                              Track Changed
0x002d  2b96                              Track Changed
0x002d  2b96                              Track Changed
0x002d  2b96                              Track Changed
0x002e  2902                              Client Characteristic Configuration
0x002e  2803                              Characteristic
0x002f  2a39                              Heart Rate Control Point
0x0030  2b97                              Track Title
0x0031  2803                              Characteristic
0x0032  2a5f                              PLX Continuous Measurement
0x0033  2b98                              Track Duration
0x0033  2902                              Client Characteristic Configuration
0x0033  2902                              Client Characteristic Configuration
0x0033  2902                              Client Characteristic Configuration
0x0033  2902                              Client Characteristic Configuration
0x0031  2902                              Client Characteristic Configuration
0x0031  2902                              Client Characteristic Configuration
0x0031  2902                              Client Characteristic Configuration
0x002e  2803                              Characteristic
0x002e  2803                              Characteristic
0x002e  2803                              Characteristic
0x002e  2803                              Characteristic
0x002f  2803                              Characteristic
0x002f  2803                              Characteristic
0x002f  2803                              Characteristic
0x002f  2803                              Characteristic
0x0032  2803                              Characteristic
0x0033  2b98                              Track Duration
0x0034  2902                              Client Characteristic Configuration
0x0032  2803                              Characteristic
0x0032  2803                              Characteristic
0x0032  2803                              Characteristic
0x0038  2803                              Characteristic
0x0039  2b9a                              Playback Speed
0x003a  2b40                              Step Counter Activity Summary Data
0x003b  2902                              Client Characteristic Configuration
0x003d  2902                              Client Characteristic Configuration
0x0039  2803                              Characteristic
0x0039  2803                              Characteristic
0x0039  2803                              Characteristic
0x003a  2902                              Client Characteristic Configuration
0x003a  2902                              Client Characteristic Configuration
0x003a  2902                              Client Characteristic Configuration
0x003b  2803                              Characteristic
0x003c  2b9b                              Seeking Speed
0x003d  2803                              Characteristic
0x003e  2a00                              Device Name
0x003f  2ba1                              Playing Order
0x0040  2a01                              Appearance
0x0040  2902                              Client Characteristic Configuration
0x0040  2902                              Client Characteristic Configuration
0x003d  2803                              Characteristic
0x003f  2803                              Characteristic
0x0040  2a01                              Appearance
0x0041  2902                              Client Characteristic Configuration
0x0042  2ba2                              Playing Orders Supported
0x003f  2803                              Characteristic
0x003f  2803                              Characteristic
0x0042  2803                              Characteristic
0x0043  2a02                              Peripheral Privacy Flag
0x0044  2ba3                              Media State
0x0045  2a03                              Reconnection Address
0x0045  2902                              Client Characteristic Configuration
0x0045  2902                              Client Characteristic Configuration
0x0045  2902                              Client Characteristic Configuration
0x0042  2803                              Characteristic
0x0042  2803                              Characteristic
0x0044  2803                              Characteristic
0x0045  2a03                              Reconnection Address
0x0046  2902                              Client Characteristic Configuration
0x0048  2902                              Client Characteristic Configuration
0x0049  046c                              Unknown
0x0044  2803                              Characteristic
0x0044  2803                              Characteristic
0x003d  2902                              Client Characteristic Configuration
0x003b  2803                              Characteristic
0x003b  2803                              Characteristic
0x003b  2803                              Characteristic
0x003e  2803                              Characteristic
0x003f  2ba1                              Playing Order
0x0040  2902                              Client Characteristic Configuration
0x003e  2803                              Characteristic
0x003e  2803                              Characteristic
0x003e  2803                              Characteristic
0x0041  2803                              Characteristic
0x0042  2ba2                              Playing Orders Supported
0x0041  2803                              Characteristic
0x0041  2803                              Characteristic
0x0041  2803                              Characteristic
0x0043  2803                              Characteristic
0x0044  2ba3                              Media State
0x0043  2803                              Characteristic
0x0043  2803                              Characteristic
0x0046  2803                              Characteristic
0x0047  2ba4                              Media Control Point
0x0048  2803                              Characteristic
0x0048  2803                              Characteristic
0x0048  2803                              Characteristic
0x0046  2803                              Characteristic
0x0046  2803                              Characteristic
0x0049  2803                              Characteristic
0x004a  2ba5                              Media Control Point Opcodes Supported
0x004b  2902                              Client Characteristic Configuration
0x0049  2803                              Characteristic
0x0049  2803                              Characteristic
0x004c  2803                              Characteristic
0x004d  2bba                              Content Control ID
0x0028  1849                              Generic Media Control
0x0028  1849                              Generic Media Control
0x0028  1849                              Generic Media Control
0x0028  1849                              Generic Media Control
0x0030  1822                              Pulse Oximeter
0x0031  2803                              Characteristic
0x0032  2a5f                              PLX Continuous Measurement
0x0033  2902                              Client Characteristic Configuration
0x0030  1822                              Pulse Oximeter
0x0030  1822                              Pulse Oximeter
0x0030  1822                              Pulse Oximeter
0x0030  1822                              Pulse Oximeter
0x0034  1111                              Fax
0x0035  2803                              Characteristic
0x0036  2b41                              Sleep Activity Instantaneous Data
0x0036  2b99                              Track Position
0x0036  2b99                              Track Position
0x0036  2b99                              Track Position
0x0036  2b99                              Track Position
0x0037  2902                              Client Characteristic Configuration
0x0034  1111                              Fax
0x0034  1111                              Fax
0x0034  1111                              Fax
0x0034  1111                              Fax
0x0038  183e                              Physical Activity Monitor
0x0039  2803                              Characteristic
0x003a  2b40                              Step Counter Activity Summary Data
0x003b  2902                              Client Characteristic Configuration
0x0038  183e                              Physical Activity Monitor
0x0038  183e                              Physical Activity Monitor
0x0038  183e                              Physical Activity Monitor
0x0038  183e                              Physical Activity Monitor
0x003c  fe35                              HUAWEI Technologies Co., Ltd
0x003d  2803                              Characteristic
0x003e  2a00                              Device Name
0x003e  2a00                              Device Name
0x003f  2803                              Characteristic
0x0040  2a01                              Appearance
0x0041  2902                              Client Characteristic Configuration
0x0042  2803                              Characteristic
0x0043  2a02                              Peripheral Privacy Flag
0x0044  2803                              Characteristic
0x0045  2a03                              Reconnection Address
0x0046  2902                              Client Characteristic Configuration
0x003c  fe35                              HUAWEI Technologies Co., Ltd
0x003c  fe35                              HUAWEI Technologies Co., Ltd
0x003c  fe35                              HUAWEI Technologies Co., Ltd
0x003c  fe35                              HUAWEI Technologies Co., Ltd
0x0047  046a                              Unknown
0x0048  2803                              Characteristic
0x0049  046c                              Unknown
0x0049  046c                              Unknown
0x0047  046a                              Unknown
0x0047  046a                              Unknown
0x0047  046a                              Unknown
0x0047  046a                              Unknown
0x005a  184c                              Generic Telephone Bearer
0x005b  2803                              Characteristic
0x005c  2bb3                              Bearer Provider Name
0x005d  2902                              Client Characteristic Configuration
0x005e  2803                              Characteristic
0x005f  2bb4                              Bearer UCI
0x0060  2803                              Characteristic
0x0061  2bb5                              Bearer Technology
0x0062  2902                              Client Characteristic Configuration
0x0063  2803                              Characteristic
0x0064  2bb6                              Bearer URI Schemes Supported List
0x0065  2902                              Client Characteristic Configuration
0x0066  2803                              Characteristic
0x0067  2bb9                              Bearer List Current Calls
0x0068  2902                              Client Characteristic Configuration
0x0069  2803                              Characteristic
0x006a  2bba                              Content Control ID
0x006b  2803                              Characteristic
0x006c  2bbb                              Status Flags
0x006d  2902                              Client Characteristic Configuration
0x006e  2803                              Characteristic
0x006f  2bbd                              Call State
0x0070  2902                              Client Characteristic Configuration
0x0071  2803                              Characteristic
0x0072  2bbe                              Call Control Point
0x0073  2902                              Client Characteristic Configuration
0x0074  2803                              Characteristic
0x0075  2bbf                              Call Control Point Optional Opcodes
0x0076  2803                              Characteristic
0x0077  2bc0                              Termination Reason
0x0078  2902                              Client Characteristic Configuration
0x0079  2803                              Characteristic
0x007a  2bc1                              Incoming Call
0x007b  2902                              Client Characteristic Configuration
0x007c  2803                              Characteristic
0x007d  2bc2                              Call Friendly Name
0x007e  2902                              Client Characteristic Configuration
0x0082  1855                              Telephony and Media Audio
0x0083  2803                              Characteristic
0x0084  2b51                              TMAP Role
0x0086  fcf1                              Google LLC
0x0087  2803                              Characteristic
0x0088  fe2c1237-8366-4814-8eb0-01de32100bea  Unknown
0x0089  2902                              Client Characteristic Configuration
0x008a  fef3                              Google LLC
0x008b  2803                              Characteristic
0x008c  00000100-0004-1000-8000-001a11000102  Unknown
0x008d  2902                              Client Characteristic Configuration
0x008e  2803                              Characteristic
0x008f  00000100-0004-1000-8000-001a11000101  Unknown
