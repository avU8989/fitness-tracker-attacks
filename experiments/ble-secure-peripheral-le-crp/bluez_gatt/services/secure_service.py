from bluez_gatt.services.gatt_service import GATTService
from bluez_gatt.characteristics.gatt_characteristic import GATTCharacteristicBase


class SecureService(GATTService):
    def __init__(self, path: str, uuid: str, primary: bool):
        super().__init__(path, uuid, primary)

        self._last_signature = b""
        self._last_challenge = b""
