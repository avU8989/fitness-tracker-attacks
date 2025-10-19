import asyncio
import struct
from bluez_peripheral.gatt.service import Service
from bluez_peripheral.gatt.characteristic import characteristic, CharacteristicFlags as CF
from common import PHYSICAL_ACTIVITY_SERVICE, STEP_COUNTER_MEASUREMENT

# based from app payload
# app payload reads UInt32, UInt16 with Little Endian
FLAG_STRIDE_LENGTH = 0x01
FLAG_DISTANCE = 0x02
FLAG_ENERGY_EXPENDED = 0x04
FLAG_MET = 0x08

# https://docs.python.org/3/library/struct.html


def build_step_payload(
        flags: int,
        step_count: int,
        duration: int,
        stride_length: int = None,
        distance: int = None,
        energy_expended: int = None,
        met: int = None,  # Metabolic Equivalent
):
    """Build step-counter payload matching the payload the app expects
    [Flags][Step Count (UInt32 LE)][Stride Length (UInt16 LE)][Distance (UInt32 LE)][Duration of Activity (UInt16 LE)][Energy Expended (UInt16 LE)][Metabolic Equivalent (UInt16 LE)]
    """

    buf = bytearray()
    buf.append(flags & 0xFF)
    buf += struct.pack("<I", step_count)  # UInt 32 Little Endian

    if flags & FLAG_STRIDE_LENGTH:
        if stride_length is None:
            raise ValueError("stride length is expected by flags")

        buf += struct.pack("<H", stride_length)  # UInt 16 Little Endian

    if flags & FLAG_DISTANCE:
        if distance is None:
            raise ValueError("distance is expected by flags")

        buf += struct.pack("<I", distance)  # UInt 32 Little Endian

    buf += struct.pack("<H", duration)  # UInt 16 Little Endian

    if flags & FLAG_ENERGY_EXPENDED:
        if energy_expended is None:
            raise ValueError("energy_expended is expected by flags")

        buf += struct.pack("<H", energy_expended)  # UInt 16 Little Endian

    if flags & FLAG_MET:
        if met is None:
            raise ValueError("Metabolic Equivalent is expected by flags")

        buf += struct.pack("<H", met)  # UInt 16 Little Endian

    return bytes(buf)


class FakePhysicalActivityMonitorService(Service):
    def __init__(self,
                 initial_steps: int = 0,
                 initial_duration: int = 0,
                 initial_stride_length: int = None,
                 initial_distance: int = None,
                 initial_energy_expenditure: int = None,
                 initial_metabolic_equivalent: int = None
                 ):
        super().__init__(PHYSICAL_ACTIVITY_SERVICE, True)
        self._step_count = initial_steps
        self._duration = initial_duration
        self._stride_length = initial_stride_length
        self._distance = initial_distance
        self._energy_expended = initial_energy_expenditure
        self._met = initial_metabolic_equivalent

        self.flags = 0x00
        if self._stride_length is not None:
            self.flags |= FLAG_STRIDE_LENGTH
        if self._distance is not None:
            self.flags |= FLAG_DISTANCE
        if self._energy_expended is not None:
            self.flags |= FLAG_ENERGY_EXPENDED
        if self._met is not None:
            self.flags |= FLAG_MET

        self._seq = 0

    # READ-Only characteristic (app performs a single read) -> not encrypted will be in plaintext and not authenticated
    @characteristic(STEP_COUNTER_MEASUREMENT, flags=CF.NOTIFY | CF.READ | CF.WRITE)
    def physical_activity_meas(self, opts):
        """Return payload for STEP COUNTER MEASUREMENT Characteristic"""

        return build_step_payload(self.flags,
                                  self._step_count,
                                  self._duration,
                                  self._stride_length,
                                  self._distance,
                                  self._energy_expended,
                                  self._met)

    def notify(self):
        payload = build_step_payload(self.flags,
                                     self._step_count,
                                     self._duration,
                                     self._stride_length,
                                     self._distance,
                                     self._energy_expended,
                                     self._met)

        # notify through characteristic.changed()
        self.physical_activity_meas.changed(payload)

    def show(self):
        print("[Physical Activity Monitor Service] flags=0x{:02x} step_count={} duration={} stride={} distance={} energy={} met={}".format(
            self.flags, self._step_count, self._duration, self._stride_length, self._distance, self._energy_expended, self._met
        ))

    # set all 5000 30 75 3750 250 8 --> test command
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
                    self._step_count = int(parts[2])
                    print(
                        "[Physical Activity Monitor Service] step count = ", self._step_count)
                    self.notify()
                    return
                if field == "duration":
                    self._duration = int(parts[2])
                    print(
                        "[Physical Activity Monitor Service] duration = ", self._duration)
                    self.notify()
                    return
                if field == "stride":
                    self._stride_length = int(parts[2])
                    print("[Physical Activity Monitor Service] stride = ",
                          self._stride_length)
                    self.notify()
                    return
                if field == "distance":
                    self._distance = int(parts[2])
                    self.flags |= FLAG_DISTANCE
                    print(
                        "[Physical Activity Monitor Service] distance = ", self._distance)
                    self.notify()
                    return
                if field == "energy":
                    self._energy_expended = int(parts[2])
                    self.flags |= FLAG_ENERGY_EXPENDED
                    self.notify()
                    return
                if field == "met":
                    self._met = int(parts[2])
                    self.flags |= FLAG_MET
                    self.notify()
                    return
                if field == "all" and len(parts) >= 8:
                    self._step_count = int(parts[2])
                    self._duration = int(parts[3])
                    self._stride_length = int(parts[4])
                    self._distance = int(parts[5])
                    self._energy_expended = int(parts[6])
                    self._met = int(parts[7])

                    self.flags = 0x00
                    if self._stride_length is not None:
                        self.flags |= FLAG_STRIDE_LENGTH
                    if self._distance is not None:
                        self.flags |= FLAG_DISTANCE
                    if self._energy_expended is not None:
                        self.flags |= FLAG_ENERGY_EXPENDED
                    if self._met is not None:
                        self.flags |= FLAG_MET

                    print("[Physical Activity Monitor Service] All values set")
                    self.notify()
                    self.show()
                    return

            print("Unknown command (type 'help')")
        except Exception as e:
            print("Command error: ", e)
