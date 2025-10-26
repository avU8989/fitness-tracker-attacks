
# --- Constants for checking values in btatt payload (the btatt payload is just on trafic to a GATT Server by nrF Connect---
PLXS_SPOT_CHECK_MEASUREMENT_SP02 = "plxs_spot_check_measurement_spo2"
PLXS_SPOT_CHECK_MEASUREMENT_PULSE_RATE = "plxs_spot_check_measurement_pulse_rate"
VENDOR_SPECIFIC_VALUE = "value"
HEARTRATE_MEASUREMENT_VALUE = "heart_rate_measurement_value_8"

# ATT OPCODE filters
# Doc for the OPCODEs meanings of Wireshark: https://github.com/boundary/wireshark/blob/master/epan/dissectors/packet-btatt.c
ATT_FILTERS = {
    "notification": "btatt.opcode == 0x1b",
    "read_response": "btatt.opcode == 0x0b",
    "read_request": "btatt.opcode == 0x0a",
}
