import argparse
from utils.logger import logger_setup
from parsers.capture_parsers import load_btatt_capture_with_filter
from parsers.att_extractor import extract_notifications_data, extract_read_response_data
from configs.att_parser_constants import ATT_FILTERS
from utils.output_writer import write_json
logger = logger_setup("btsnoop_parser")


def main():
    parser = argparse.ArgumentParser(
        description="Parse BLE ATT packets (Read, Write, Notify)")
    parser.add_argument("infile",
                        help="Input .pcap or .btsnoop file")
    parser.add_argument("-o", "--output", help="Output file path",
                        default="output/att_parsed_output.json")

    args = parser.parse_args()

    # each opcode has a distinct meaning
    # e.g. for our Heart Rate Measurement --> peripheral notifys --> captured file will show OPCODE "0x1b" --> that means "Handle Value Notification"
    # so we want to filter after btatt.opcode == 0x1b, that will show us all the Notify Payloads of our GATT

    output_data = []

    # ---Notifications Packets---
    notification_captures = load_btatt_capture_with_filter(
        # OPCODE - Handle Value Notification
        args.infile, ATT_FILTERS.get("notification"))

    for i, notify_cap in enumerate(notification_captures):
        entry = extract_notifications_data(notify_cap)

        if i >= 50:
            logger.info(
                "Stopping after 50 notification entries (debug limit)")
            break

        if entry:
            output_data.append(entry)

    # ---Read Response Packets---
    read_response_captures = load_btatt_capture_with_filter(
        # OPCODE - Read Response
        args.infile, ATT_FILTERS.get("read_response")
    )

    for read_response_cap in read_response_captures:
        entry = extract_read_response_data(read_response_cap)

        if entry:
            output_data.append(entry)

    # now we want to generate an output file with the json format
    #    "src_addr": ,
    #    "dst_addr": ,
    #    "opcode": ,
    #    "handle": ,
    #    "service_uuid16": ,
    #    "char_uuid16": ,
    #    "values": {}

    write_json(output_data, args.output)


if __name__ == "__main__":
    main()
