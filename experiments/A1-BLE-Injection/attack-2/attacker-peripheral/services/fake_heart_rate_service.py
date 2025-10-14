import asyncio
import time
from bluez_peripheral.gatt.service import Service
from bluez_peripheral.gatt.characteristic import characteristic, CharacteristicFlags as CF
from common import HEARTRATE_SERVICE, HEARTRATE_MEASUREMENT

MAX_HEARTRATE_RAMP = 500
MIN_HEARTRATE_RAMP = 20
MAX_HEARTRATE = 999
MIN_HEARTRATE = 0


class FakeHeartRateService(Service):
    def __init__(self):
        super().__init__(HEARTRATE_SERVICE, True)
        self._bpm = MIN_HEARTRATE_RAMP
        self._seq = 0
        self._dir = 1  # ramp direction
        self.ramp_step = 2
        self.manualHR = 0
        self._last = time.time()

    # simple 8-bit heartrate measurement payload
    @characteristic(HEARTRATE_MEASUREMENT, CF.NOTIFY, CF.READ, CF.WRITE)
    def heart_rate_measurement(self, opts):
        flags = 0x00
        return bytes([flags, self._bpm & 0xFF])

    def notify_hr(self):
        flags = 0x00
        self.heart_rate_measurement.changed(bytes([flags, self._bpm & 0xFF]))

    async def start(self):
        """Tick once per second and send notification if subscribed"""
        while True:
            if self.manualHR > 0:
                self._bpm = max(MIN_HEARTRATE, min(
                    MAX_HEARTRATE, int(self.manualHR)))
            else:
                # logic to ramp heartrate up & down
                self._bpm += self._dir * self.ramp_step
                if self._bpm >= MAX_HEARTRATE_RAMP:
                    self._bpm = MAX_HEARTRATE_RAMP
                    self._dir = -1
                elif self._bpm <= MIN_HEARTRATE_RAMP:
                    self._bpm = MIN_HEARTRATE_RAMP
                    self._dir = +1

            # send notification each second
            self.notify_hr()
            await asyncio.sleep(1.0)
