
from common import int_sFloat_le, PULSEOXIMETER_SERVICE, PLX_CONT_MEAS
from bluez_peripheral.gatt.service import Service
from bluez_peripheral.gatt.characteristic import characteristic, CharacteristicFlags as CF

# https://www.bluetooth.com/wp-content/uploads/Files/Specification/HTML/PLXP_v1.0.1/out/en/index-en.html


class FakePulseOximeterService(Service):
    def __init__(self):
        super().__init__(PULSEOXIMETER_SERVICE, True)
        self._spo2 = 20  # unrealistic peripheral capillary oxygen saturation
        self._seq = 0
        self._bpm = 250  # unrealistic heartrate
        self._subscribed = False

    # READ-Only characteristic (app performs a single read)
    @characteristic(PLX_CONT_MEAS, CF.READ)
    def count_measurement(self, opts):
        # used for reads --> return current value as single byte percent
        # attacker expects that the app will definetly receive a spo2 field from the real ble device
        flags = 0x00
        payload = bytes([flags]) + int_sFloat_le(self._spo2) + \
            int_sFloat_le(self._bpm)
        return payload
