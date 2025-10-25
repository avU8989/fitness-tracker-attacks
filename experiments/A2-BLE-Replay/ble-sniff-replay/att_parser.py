# btsnoop-based ATT Write extraction

import json
import argparse
import os
import pyshark  # wrapper for tshark, allowing python packet parsing
from pyshark import FileCapture
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger(__name__)


def load_gatt_map(path: str):
    """Load JSON file mapping device addresses e.g :
    {
        "Peripheral MAC ADDRESS": {
            "002a": "Heart Rate Measurement",
            ...
        }
    }
    """

    if not path or not os.path.exists(path):
        print("Gatt MAP not found: ", path)


def parse_capture(infile):
    '''Display all captured gatt attributes'''

    # you can also specify on wireshark which source address it should capture --> the source address is in our case the MAC Address of our BLE Peripheral
    cap = pyshark.FileCapture(infile, display_filter="btatt")

    return cap


def parse_capture_filter(infile, display_filter):
    '''Filter after your query'''
    cap = pyshark.FileCapture(infile, display_filter=display_filter)

    return cap


# --- Constants for checking values in btatt payload (the btatt payload is just on trafic to a GATT Server by nrF Connect---
PLXS_SPOT_CHECK_MEASUREMENT_SP02 = "plxs_spot_check_measurement_spo2"
PLXS_SPOT_CHECK_MEASUREMENT_PULSE_RATE = "plxs_spot_check_measurement_pulse_rate"
VENDOR_SPECIFIC_VALUE = "value"
HEARTRATE_MEASUREMENT_VALUE = "heart_rate_measurement_value_8"


def main():
    # Generic Attribute Profile (GATT) handles services and profiles

    parser = argparse.ArgumentParser(
        description="Parse BLE ATT packets (Read, Write, Notify)")
    parser.add_argument("infile",
                        help="Input .pcap or .btsnoop file")
    parser.add_argument("-g", "--gattmap", help="Path to gatt_map.json",
                        default="gatt_map.json")
    args = parser.parse_args()

    # btatt opcode --> refers to Opcode of Attribute Protocol (ATT)
    # What is ATT?
    # An ATT is structured in four different sections: 16-bit handle that labels the attribute (in our case 0x002a), a UUID that defines the type of the attribute (2a37 - Heart Rate Measurement, permissions e.g.(flags), a value of certain length e.g. (90))
    # ATT lets device show its attributes to others like services, characteristics and their values

    # each opcode has a distinct meaning
    # Doc for the OPCODEs meanings of Wireshark: https://github.com/boundary/wireshark/blob/master/epan/dissectors/packet-btatt.c
    # e.g. for our Heart Rate Measurement --> peripheral notifys --> captured file will show OPCODE "0x1b" --> that means "Handle Value Notification"

    # so we want to filter after btatt.opcode == 0x1b, that will show us all the Notify Payloads of our GATT

    # Initialize captures we want to filter
    notification_captures = parse_capture_filter(
        args.infile, "btatt.opcode == 0x1b")  # OPCODE - Handle Value Notification

    read_response_captures = parse_capture_filter(
        args.infile, "btatt.opcode == 0x0b"  # OPCODE - Read Response
    )

    read_request_captures = parse_capture_filter(
        args.infile, "btatt.opcode == 0x0a"  # OPCODE - Read Request
    )

    # now we want it to generate an output file with format
    # [OPCODE], [Characteristic UUID], [Name of the Char UUID], [Value]

    output_data = []

    # extract output data from notification captures
    for notify_cap in notification_captures:
        src_addr = ""
        dst_addr = ""
        if hasattr(notify_cap, "bthci_acl"):
            src_addr = getattr(notify_cap.bthci_acl, "src_bd_addr", None)

        if hasattr(notify_cap, "bthci_acl"):
            dst_addr = getattr(notify_cap.bthci_acl, "dst_bd_addr", None)

        if hasattr(notify_cap, "btatt"):
            opcode = getattr(notify_cap.btatt, "opcode", None)
            service_uuid = getattr(notify_cap.btatt, "service_uuid16", "")
            uuid16 = getattr(notify_cap.btatt, "uuid16", "")
            handle = getattr(notify_cap.btatt, "handle", None)

            entry = {
                "src_addr": src_addr,
                "dst_addr": dst_addr,
                "opcode": opcode,
                "handle": handle,
                "service_uuid16": service_uuid,
                "char_uuid16": uuid16,
                "values": {}
            }

            if hasattr(notify_cap.btatt, HEARTRATE_MEASUREMENT_VALUE):
                entry["values"]["bpm"] = notify_cap.btatt.heart_rate_measurement_value_8.replace(
                    ":", "")

            # just save the first 50 entries of notification captures --> in my pcap i have roughly 1174 entries
            if (len(output_data) >= 50):
                logger.info(
                    "Stopping after 50 notification entries (debug limit)")
                break

            output_data.append(entry)

        else:
            print("No btatt attribute in this entry")
            continue

    for read_respone_cap in read_response_captures:
        src_addr = ""
        dst_addr = ""
        if hasattr(notify_cap, "bthci_acl"):
            src_addr = getattr(notify_cap.bthci_acl, "src_bd_addr", None)

        if hasattr(notify_cap, "bthci_acl"):
            dst_addr = getattr(notify_cap.bthci_acl, "dst_bd_addr", None)

        if hasattr(read_respone_cap, "btatt"):

            opcode = getattr(read_respone_cap.btatt, "opcode", None)
            service_uuid = getattr(
                read_respone_cap.btatt, "service_uuid16", "")
            uuid16 = getattr(read_respone_cap.btatt, "uuid16", "")
            handle = getattr(read_respone_cap.btatt, "handle", None)

            entry = {
                "src_addr": src_addr,
                "dst_addr": dst_addr,
                "opcode": opcode,
                "handle": handle,
                "service_uuid16": service_uuid,
                "char_uuid16": uuid16,
                "values": {}
            }

            if hasattr(read_respone_cap.btatt, PLXS_SPOT_CHECK_MEASUREMENT_SP02):
                entry["values"]["spo2"] = float(
                    read_respone_cap.btatt.plxs_spot_check_measurement_spo2)

            if hasattr(read_respone_cap.btatt, PLXS_SPOT_CHECK_MEASUREMENT_PULSE_RATE):
                entry["values"]["bpm"] = int(
                    read_respone_cap.btatt.plxs_spot_check_measurement_pulse_rate)

            if hasattr(read_respone_cap.btatt, VENDOR_SPECIFIC_VALUE):
                entry["values"]["raw"] = read_respone_cap.btatt.value.replace(
                    ":", "")

            output_data.append(entry)

    out_path = "att_parsed_output.json"
    with open(out_path, "w") as f:
        json.dump(output_data, f, indent=2)

    logger.info(f"[+] Parsed {len(output_data)} entries saved to {out_path}")


if __name__ == "__main__":
    main()
