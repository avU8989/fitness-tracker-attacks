
from bluez_gatt.characteristics.gatt_characteristic import GATTCharacteristicBase


class SleepMeasurementCharacteristic(GATTCharacteristicBase):
    def __init__(self, path: str, uuid: str, service_path: str, flags: list[str]):
        super().__init__(path, uuid, service_path, flags)

        # Default Values
        self._stage = 1
        self._duration_min = 60
        self._hr = 70
        self._rem_pct = 33
        self._light_pct = 33
        self._deep_pct = 33

        self._value = self.build_payload()

    def build_payload(self) -> bytes:
        # Mocked sleep data no official Bluetooth SIG spec --> like vendor-specific service
        # [Stage][Duration_Lo][Duration_Hi][HR][REM%][Light%][Deep%]
        """Pack the fields in a 7 byte payload"""
        # clamp values to valid ranges
        stage = int(self._stage) & 0xFF  # mask at 8 Bits
        duration = int(self._duration_min) & 0XFFFF  # mask at 16 Bits
        hr = int(self._hr) & 0xFF
        rem_pct = int(self._rem_pct) & 0XFF
        light_pct = int(self._light_pct) & 0XFF
        deep_pct = int(self._deep_pct) & 0XFF

        duration_lo = duration & 0xFF
        duration_hi = (duration >> 8) & 0xFF

        return bytes([stage, duration_lo, duration_hi, hr, rem_pct, light_pct, deep_pct])

    def notify_update(self):
        self._value = self.build_payload()
        self.emit_properties_changed({
            "Value": self._value,
            "Notifying": True
        })
