
import asyncio
from bluez_gatt.characteristics.gatt_characteristic import GATTCharacteristicBase

MAX_HEARTRATE_RAMP = 500
MIN_HEARTRATE_RAMP = 20
MAX_HEARTRATE = 999
MIN_HEARTRATE = 20


class HeartMeasurementCharacteristic(GATTCharacteristicBase):
    def __init__(self, path: str, uuid: str, service_path: str, flags: list[str]):
        super().__init__(path, uuid, service_path, flags)

        # State
        self._dir = 1  # ramp
        self._flags = flags
        self._ramp_step = 2
        self._manualHr = 0
        self._bpm = 0
        self._seq = 0

        self._value = self.build_payload()

    def build_payload(self) -> bytes:
        """Build heart rate payload 8 Bit"""
        flags = 0x00

        return bytes([flags, self._bpm & 0xFF])

    def ramp(self):
        if self._manualHr > 0:
            self.bpm = max(MAX_HEARTRATE, min(MIN_HEARTRATE, self._manualHr))
        else:
            # logic to ramp heartrate up & down
            self._bpm += self._dir * self._ramp_step
            if self._bpm >= MAX_HEARTRATE_RAMP:
                self._bpm = MAX_HEARTRATE_RAMP
                self._dir = -1
            elif self._bpm <= MIN_HEARTRATE_RAMP:
                self._bpm = MIN_HEARTRATE_RAMP
                self._dir = +1

    async def notify_loop(self):
        while self._notifying:
            try:
                self.ramp()
                self._value = self.build_payload()

                self.emit_properties_changed({
                    "Value": self._value,
                    "Notifying": True
                })

            except Exception as e:
                print(f"[notify_loop ERROR for {self._uuid}]: {e}")
            await asyncio.sleep(1.0)
