# common.py
# constants & helper utils

def int_sFloat_le(value: int) -> bytes:
    # encode integer value as IEEE-11073 SFLOAT (exp=0, mantissa = value)
    mant = value & 0x0fff
    exp = 0
    raw = (exp << 12) | mant
    return bytes([raw & 0xff, (raw >> 8) & 0xff])
