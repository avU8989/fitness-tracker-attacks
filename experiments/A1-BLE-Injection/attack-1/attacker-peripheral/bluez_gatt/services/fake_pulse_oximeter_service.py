from bluez_gatt.services.gatt_service import GATTService
from bluez_gatt.characteristics.gatt_characteristic import GATTCharacteristicBase
from bluez_gatt.characteristics.pulse_oximeter_meas_char import PulseOximeterMeasurementCharacteristic


class FakePulseOximeterService(GATTService):
    def __init__(self, path: str, uuid: str, characteristics: list[GATTCharacteristicBase]):
        super().__init__(path, uuid, True)
        self.characteristics = characteristics
