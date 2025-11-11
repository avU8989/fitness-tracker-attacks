from bluez_gatt.characteristics.gatt_characteristic import GATTCharacteristicBase
from utils.common import int_sFloat_le


class PulseOximeterMeasurementCharacteristic(GATTCharacteristicBase):
    def __init__(self, path: str, uuid: str, service_path: str, flags: list[str]):
        super().__init__(path, uuid, service_path, flags)
        self._spo2 = 20  # unrealistic peripheral capillary oxygen saturation
        self._seq = 0
        self._bpm = 250  # unrealistic heartrate

        self._value = self.build_payload()

    def build_payload(self) -> bytes:
        flags = 0x00
        payload = bytes([flags]) + int_sFloat_le(self._spo2) + \
            int_sFloat_le(self._bpm)

        return payload
