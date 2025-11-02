
from bluez_gatt.characteristics.gatt_characteristic import GATTCharacteristicBase
import struct
# based from app payload
# app payload reads UInt32, UInt16 with Little Endian
FLAG_STRIDE_LENGTH = 0x01
FLAG_DISTANCE = 0x02
FLAG_ENERGY_EXPENDED = 0x04
FLAG_MET = 0x08


class StepCounterCharacteristic(GATTCharacteristicBase):
    def __init__(self, path: str, uuid: str, service_path: str, flags: list[str]):
        super().__init__(path, uuid,
                         service_path, flags)
        # Unrealistic Default Values
        self._step_count = 999
        self._duration = 500
        self._stride_length = 20
        self._distance = 999
        self._energy_expended = 10
        self._met = 0

        self.flags = 0x00
        if self._stride_length is not None:
            self.flags |= FLAG_STRIDE_LENGTH
        if self._distance is not None:
            self.flags |= FLAG_DISTANCE
        if self._energy_expended is not None:
            self.flags |= FLAG_ENERGY_EXPENDED
        if self._met is not None:
            self.flags |= FLAG_MET

        self._value = self.build_payload()

    def build_payload(self) -> bytes:
        """Build step-counter payload matching the payload the app expects
        [Flags][Step Count (UInt32 LE)][Stride Length (UInt16 LE)][Distance (UInt32 LE)][Duration of Activity (UInt16 LE)][Energy Expended (UInt16 LE)][Metabolic Equivalent (UInt16 LE)]
        """

        buf = bytearray()
        buf.append(self.flags & 0xFF)
        buf += struct.pack("<I", self._step_count)  # UInt 32 Little Endian

        if self.flags & FLAG_STRIDE_LENGTH:
            if self._stride_length is None:
                raise ValueError("stride length is expected by flags")

            # UInt 16 Little Endian
            buf += struct.pack("<H", self._stride_length)

        if self.flags & FLAG_DISTANCE:
            if self._distance is None:
                raise ValueError("distance is expected by flags")

            buf += struct.pack("<I", self._distance)  # UInt 32 Little Endian

        buf += struct.pack("<H", self._duration)  # UInt 16 Little Endian

        if self.flags & FLAG_ENERGY_EXPENDED:
            if self._energy_expended is None:
                raise ValueError("energy_expended is expected by flags")

            # UInt 16 Little Endian
            buf += struct.pack("<H", self._energy_expended)

        if self.flags & FLAG_MET:
            if self._met is None:
                raise ValueError("Metabolic Equivalent is expected by flags")

            buf += struct.pack("<H", self._met)  # UInt 16 Little Endian

        return bytes(buf)

    def notify_update(self):
        self._value = self.build_payload()
        self.emit_properties_changed({
            "Value": self._value,
            "Notifying": True
        })
