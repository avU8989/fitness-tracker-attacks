from configs.constants import ATT_FILTERS, HEARTRATE_MEASUREMENT_VALUE, PLXS_SPOT_CHECK_MEASUREMENT_SP02, PLXS_SPOT_CHECK_MEASUREMENT_PULSE_RATE, VENDOR_SPECIFIC_VALUE

# btatt opcode --> refers to Opcode of Attribute Protocol (ATT)
# What is ATT?
# An ATT is structured in four different sections: 16-bit handle that labels the attribute (in our case 0x002a),
# a UUID that defines the type of the attribute (2a37 - Heart Rate Measurement, permissions e.g.(flags), a value of certain length e.g. (90))
# ATT lets device show its attributes like services and characteristics to others


def _base_entry(packet):
    """Return a base dictionary for a BLE ATT packet"""
    btatt = getattr(packet, "btatt", None)
    bthci_acl = getattr(packet, "bthci_acl", None)

    return {
        "src_addr": getattr(bthci_acl, "src_bd_addr", None),
        "dst_addr": getattr(bthci_acl, "dst_bd_addr", None),
        "opcode": getattr(btatt, "opcode", None),
        "handle": getattr(btatt, "handle", None),
        "service_uuid16": getattr(btatt, "service_uuid16", ""),
        "char_uuid16": getattr(btatt, "uuid16", ""),
        "values": {}
    }


def extract_notifications_data(packet):
    """Extract data from a handle notification (0x1b) packets"""
    entry = _base_entry(packet)
    btatt = getattr(packet, "btatt", None)

    if btatt is None:
        return None

    if hasattr(btatt, HEARTRATE_MEASUREMENT_VALUE):
        entry["values"]["bpm"] = btatt.heart_rate_measurement_value_8.replace(
            ":", "")

    return entry


def extract_read_response_data(packet):
    """Extract data from read response (0x0b) packets"""
    entry = _base_entry(packet)
    btatt = getattr(packet, "btatt", None)

    if btatt is None:
        return None

    if hasattr(btatt, PLXS_SPOT_CHECK_MEASUREMENT_SP02):
        entry["values"]["spo2"] = float(
            btatt.plxs_spot_check_measurement_spo2)

    if hasattr(btatt, PLXS_SPOT_CHECK_MEASUREMENT_PULSE_RATE):
        entry["values"]["bpm"] = int(
            btatt.plxs_spot_check_measurement_pulse_rate)

    if hasattr(btatt, VENDOR_SPECIFIC_VALUE):
        entry["values"]["raw"] = btatt.value.replace(
            ":", "")

    return entry
