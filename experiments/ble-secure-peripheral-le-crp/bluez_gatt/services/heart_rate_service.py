from bluez_gatt.services.gatt_service import GATTService
from bluez_gatt.characteristics.gatt_characteristic import GATTCharacteristicBase


class HeartRateService(GATTService):
    def __init__(self, path: str, service_uuid: str, characteristics: list[GATTCharacteristicBase]):
        super().__init__(path, service_uuid, True)
        self._characteristics = characteristics
