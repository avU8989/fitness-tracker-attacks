import pyshark


def load_btatt_capture(infile):
    '''Display all captured gatt attributes'''

    # you can also specify on wireshark which source address it should capture --> the source address is in our case the MAC Address of our BLE Peripheral
    cap = pyshark.FileCapture(infile, display_filter="btatt")

    return cap


def load_btatt_capture_with_filter(infile, display_filter):
    '''Filter after your query'''
    cap = pyshark.FileCapture(infile, display_filter=display_filter)

    return cap
