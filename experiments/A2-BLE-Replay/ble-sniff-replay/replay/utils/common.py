# common.py
# constants & helper utils

def int_sFloat_le(value: int) -> bytes:
    """encode integer value as IEEE-11073 SFLOAT (exp=0, mantissa = value)"""
    mant = value & 0x0fff
    exp = 0
    raw = (exp << 12) | mant
    return bytes([raw & 0xff, (raw >> 8) & 0xff])


def expand_uuid16(uuid16: str) -> str:
    """Convert 16-bit BLE UUID to full 128-bit UUID."""
    if not uuid16 or not uuid16.startswith("0x"):
        return uuid16
    return f"0000{uuid16[2:]}-0000-1000-8000-00805f9b34fb"
