from bluez_gatt.services.gatt_service import GATTService
from bluez_gatt.characteristics.gatt_characteristic import GATTCharacteristicBase
from bluez_gatt.characteristics.physical_activty_meas_char import StepCounterCharacteristic


class FakePhysicalActivityMonitorService(GATTService):
    # for now only handle one characteristic in service
    def __init__(self, path: str, service_uuid: str, characteristic: StepCounterCharacteristic):
        super().__init__(path, service_uuid, True)
        self._step_char = characteristic

    def set_steps(self, value: int):
        self._step_char._step_count = value
        self._step_char.notify_update()

    def set_duration(self, value: int):
        self._step_char._duration = value
        self._step_char.notify_update()

    def set_stride_length(self, value: int):
        self._step_char._stride_length = value
        self._step_char.notify_update()

    def set_distance(self, value: int):
        self._step_char._distance = value
        self._step_char.notify_update()

    def set_energy_expended(self, value: int):
        self._step_char._energy_expended = value
        self._step_char.notify_update()

    def set_met(self, value: int):
        self._step_char._met = value
        self._step_char.notify_update()

    def set_all(self, step_count, duration, stride_length, distance, energy, met):
        self._step_char._step_count = step_count
        self._step_char._duration = duration
        self._step_char._stride_length = stride_length
        self._step_char._distance = distance
        self._step_char._energy_expended = energy
        self._step_char._met = met
        self._step_char.notify_update()

    def show(self):
        print("[Physical Activity Monitor Service] flags=0x{:02x} step_count={} duration={} stride={} distance={} energy={} met={}".format(
            0x00, self._step_char._step_count, self._step_char._duration, self._step_char._stride_length, self._step_char._distance, self._step_char._energy_expended, self._step_char._met
        ))

    def handle_command(self, line: str):
        """stdin control for READ-only use
            Commands:
            set steps <n>
            set duration <min>
            set stride <m>
            set distance <m>
            set energy <kJ>
            set met <val>
            set all <steps> <duration> <stride_length> <distance> <energy> <met>
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
                print("set steps <n>")
                print("set duration <min>")
                print("set stride <m>")
                print("set distance <m>")
                print("set energy <kJ>")
                print("set met <val>")
                print(
                    "set all <steps> <duration> <stride_length> <distance> <energy> <met>")
                print("help")
                print("show")
                return
            if cmd == "show":
                self.show()
                return
            if cmd == "set" and len(parts) >= 3:
                # steps, duration, stride, distance, energy, met, all
                field = parts[1].lower()

                if field == "steps":
                    self.set_steps(int(parts[2]))
                    print(
                        "[Physical Activity Monitor Service] step count = ", self._step_char._step_count)
                    return
                if field == "duration":
                    self.set_duration(int(parts[2]))
                    print(
                        "[Physical Activity Monitor Service] duration = ", self._step_char._duration)
                    return
                if field == "stride":
                    self.set_stride_length(int(parts[2]))
                    print("[Physical Activity Monitor Service] stride = ",
                          self._stride_length)
                    return
                if field == "distance":
                    self.set_distance(int(parts[2]))
                    print(
                        "[Physical Activity Monitor Service] distance = ", self._step_char._distance)
                    return
                if field == "energy":
                    self.set_energy_expended(int(parts[2]))
                    print(
                        "[Physical Activity Monitor Service] energy_expended = ", self._step_char._energy_expended)
                    return
                if field == "met":
                    self.set_met(int(parts[2]))
                    print(
                        "[Physical Activity Monitor Service] met = ", self._step_char._met)
                    return
                if field == "all" and len(parts) >= 8:
                    vals = list(map(int, parts[2:8]))

                    print("[Physical Activity Monitor Service] All values set")
                    self.set_all(*vals)
                    self.show()
                    return

            print("Unknown command (type 'help')")
        except Exception as e:
            print("Command error: ", e)
