from bluez_gatt.services.gatt_service import GATTService
from bluez_gatt.characteristics.gatt_characteristic import GATTCharacteristicBase


class PulseOximeterService(GATTService):
    def __init__(self, path: str, uuid: str, characteristics: list[GATTCharacteristicBase]):
        super().__init__(path, uuid, True)
        self.characteristics = characteristics
