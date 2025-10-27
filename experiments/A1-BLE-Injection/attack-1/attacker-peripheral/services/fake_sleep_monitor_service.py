import asyncio
from common import SLEEP_MONITOR_SERVICE, SLEEP_MEASUREMENT
from bluez_peripheral.gatt.service import Service
from bluez_peripheral.gatt.characteristic import characteristic, CharacteristicFlags as CF


def build_sleep_payload(stage: int, duration_min: int, hr: int, rem_pct: int, light_pct: int, deep_pct: int) -> bytes:
    # Mocked sleep data no official Bluetooth SIG spec --> like vendor-specific service
    # [Stage][Duration_Lo][Duration_Hi][HR][REM%][Light%][Deep%]
    """Pack the fields in a 7 byte payload"""
    # clamp values to valid ranges
    stage = int(stage) & 0xFF  # mask at 8 Bits
    duration = int(duration_min) & 0XFFFF  # mask at 16 Bits
    hr = int(hr) & 0xFF
    rem_pct = int(rem_pct) & 0XFF
    light_pct = int(light_pct) & 0XFF
    deep_pct = int(deep_pct) & 0XFF

    duration_lo = duration & 0xFF
    duration_hi = (duration >> 8) & 0xFF

    return bytes([stage, duration_lo, duration_hi, hr, rem_pct, light_pct, deep_pct])


class FakeSleepMonitorService(Service):
    def __init__(self, initial_stage: int = 1,
                 initial_duration_min: int = 60,
                 initial_hr: int = 70,
                 initial_rem_pct: int = 33,
                 initial_light_pct: int = 33,
                 initial_deep_pct: int = 34,
                 ):
        super().__init__(SLEEP_MONITOR_SERVICE, True)
        self._stage = initial_stage
        self._duration_min = initial_duration_min
        self._hr = initial_hr
        self._rem_pct = initial_rem_pct
        self._light_pct = initial_light_pct
        self._deep_pct = initial_deep_pct

    @characteristic(SLEEP_MEASUREMENT, flags=CF.NOTIFY | CF.READ | CF.WRITE)
    def sleep_activity_meas(self, opts):
        return build_sleep_payload(self._stage, self._duration_min, self._hr, self._rem_pct, self._light_pct, self._deep_pct)

    def notify(self):
        payload = build_sleep_payload(
            self._stage,
            self._duration_min,
            self._hr,
            self._rem_pct,
            self._light_pct,
            self._deep_pct)

        # notify through characteristic.changed()
        self.sleep_activity_meas.changed(payload)

    def show(self):
        print("[Sleep Activity Monitor Service] stage={} duration={} hr={} rem_percent={} light_percent={} deep_percent={}".format(
            self._stage, self._duration_min, self._hr, self._rem_pct, self._light_pct, self._deep_pct
        ))

    # example command : set all 2 480 65 20 50 30
    async def handle_command(self, line: str):
        """stdin control for READ-only use
            Commands: 
            set stage <n>
            set duration <min>
            set hr <bpm>
            set rem <percent>
            set light <percent>
            set deep <percent>
            set all <stage> <duration> <hr> <rem_percent> <light_percent> <deep_percent>
            show 
            help
            exit
        """

        # user exits the command line skip
        if line is None:
            return

        # clean user input of leading/trailing whitespaces, line empty skip
        line = line.strip()
        if not line:
            return

        # split on the whitespaces
        parts = line.split()
        # set, show, help, exit command
        cmd = parts[0].lower()

        try:
            if cmd == "help":
                print("Commands: ")
                print("set stage <n>")
                print("set duration <min>")
                print("set hr <bpm>")
                print("set rem <percent>")
                print("set light <percent>")
                print("set deep <percent>")
                print(
                    "set all <stage> <duration> <hr> <rem_percent> <light_percent> <deep_percent>")
                print("help")
                print("show")
                return
            if cmd == "show":
                self.show()
                return
            if cmd == "set" and len(parts) >= 3:
                # steps, duration, stride, distance, energy, met, all
                field = parts[1].lower()

                if field == "stage":
                    self._stage = int(parts[2])
                    print("[Sleep Activity Monitor Service] stage = ", self._stage)
                    self.notify()
                    return
                if field == "duration":
                    self._duration_min = int(parts[2])
                    print("[Sleep Activity Monitor Service] duration = ",
                          self._duration_min, " min")
                    self.notify()
                    return
                if field == "hr":
                    self._hr = int(parts[2])
                    print("[Sleep Activity Monitor Service] hr = ",
                          self._hr, " bpm")
                    self.notify()
                    return
                if field == "rem":
                    self._rem_pct = int(parts[2])
                    print("[Sleep Activity Monitor Service] REM = ",
                          self._rem_pct, " %")
                    self.notify()
                    return
                if field == "light":
                    self._light_pct = int(parts[2])
                    print("[Sleep Activity Monitor Service] LIGHT = ",
                          self._light_pct, " %")
                    self.notify()
                    return
                if field == "deep":
                    self._deep_pct = int(parts[2])
                    print("[Sleep Activity Monitor Service] DEEP = ",
                          self._deep_pct, " %")
                    self.notify()
                    return
                if field == "all" and len(parts) >= 8:
                    self._stage = int(parts[2])
                    self._duration_min = int(parts[3])
                    self._hr = int(parts[4])
                    self._rem_pct = int(parts[5])
                    self._light_pct = int(parts[6])
                    self._deep_pct = int(parts[7])

                    print("[Sleep Activity Monitor Service] All values set")
                    self.notify()
                    self.show()
                    return

            print("[Sleep Activity Monitor Service] Unknown command (type 'help')")
        except Exception as e:
            print("[Sleep Activity Monitor Service] Command error: ", e)
