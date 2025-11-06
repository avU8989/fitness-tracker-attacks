from bluez_gatt.services.gatt_service import GATTService
from bluez_gatt.characteristics.gatt_characteristic import GATTCharacteristicBase
from bluez_gatt.characteristics.sleep_activity_meas_char import SleepMeasurementCharacteristic


class SleepMonitorService(GATTService):
    # for now only handle one characteristic in service
    def __init__(self, path: str, service_uuid: str, characteristic: SleepMeasurementCharacteristic):
        super().__init__(path, service_uuid, True)
        self._sleep_meas_char = characteristic

    def set_stage(self, stage: int):
        self._sleep_meas_char._stage = stage
        self._sleep_meas_char.notify_update()

    def set_duration(self, duration: int):
        # duration minutes
        self._sleep_meas_char._duration_min = duration
        self._sleep_meas_char.notify_update()

    def set_hr(self, hr: int):
        self._sleep_meas_char._hr = hr
        self._sleep_meas_char.notify_update()

    def set_rem_sleep(self, rem_percentage: int):
        self._sleep_meas_char._rem_pct = rem_percentage
        self._sleep_meas_char.notify_update()

    def set_light_sleep(self, light_percentage: int):
        self._sleep_meas_char._light_pct = light_percentage
        self._sleep_meas_char.notify_update()

    def set_deep_sleep(self, deep_percentage: int):
        self._sleep_meas_char._deep_pct = deep_percentage
        self._sleep_meas_char.notify_update()

    def set_all(self, stage: int, duration: int, hr: int, rem_pct: int, light_pct: int, deep_pct: int):
        self._sleep_meas_char._stage = stage
        self._sleep_meas_char._duration_min = duration
        self._sleep_meas_char._hr = hr
        self._sleep_meas_char._rem_pct = rem_pct
        self._sleep_meas_char._light_pct = light_pct
        self._sleep_meas_char._deep_pct = deep_pct
        self._sleep_meas_char.notify_update()

    def show(self):
        print("[Sleep Activity Monitor Service] stage={} duration={} hr={} rem_percent={} light_percent={} deep_percent={}".format(
            self._sleep_meas_char._stage, self._sleep_meas_char._duration_min, self._sleep_meas_char._hr, self._sleep_meas_char._rem_pct, self._sleep_meas_char._light_pct, self._sleep_meas_char._deep_pct
        ))

    # example command : set all 2 480 65 20 50 30
    def handle_command(self, line: str):
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
                    self.set_stage(int(parts[2]))
                    print("[Sleep Activity Monitor Service] stage = ",
                          self._sleep_meas_char._stage)

                    return
                if field == "duration":
                    self.set_duration(int(parts[2]))
                    print("[Sleep Activity Monitor Service] duration = ",
                          self._sleep_meas_char._duration_min, " min")
                    return
                if field == "hr":
                    self.set_hr(int(parts[2]))
                    print("[Sleep Activity Monitor Service] hr = ",
                          self._sleep_meas_char._hr, " bpm")
                    return
                if field == "rem":
                    self.set_rem_sleep(int(parts[2]))
                    print("[Sleep Activity Monitor Service] REM = ",
                          self._sleep_meas_char._rem_pct, " %")
                    return
                if field == "light":
                    self.set_light_sleep(int(parts[2]))
                    print("[Sleep Activity Monitor Service] LIGHT = ",
                          self._sleep_meas_char._light_pct, " %")
                    return
                if field == "deep":
                    self.set_deep_sleep(int(parts[2]))
                    print("[Sleep Activity Monitor Service] DEEP = ",
                          self._sleep_meas_char._deep_pct, " %")
                    return
                if field == "all" and len(parts) >= 8:
                    vals = list(map(int, parts[2:8]))

                    print("[Sleep Activity Monitor Service] All values set")
                    self.set_all(*vals)
                    self.show()
                    return

            print("[Sleep Activity Monitor Service] Unknown command (type 'help')")
        except Exception as e:
            print("[Sleep Activity Monitor Service] Command error: ", e)
