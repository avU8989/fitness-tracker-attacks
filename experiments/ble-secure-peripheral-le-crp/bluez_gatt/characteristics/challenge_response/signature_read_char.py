from bluez_gatt.characteristics.gatt_characteristic import GATTCharacteristicBase
from cryptography.hazmat.primitives.asymmetric.utils import decode_dss_signature
from config.security_cfg import DEVICE_PRIVATE_KEY, N_P256
from utils.common import ts
from bluez_gatt.services.secure_service import SecureService


class SignatureCharacteristic(GATTCharacteristicBase):
    def __init__(self, path: str, uuid: str, service: SecureService, flags: list[str]):
        super().__init__(path, uuid, service._path, flags)
        self._service = service

    def on_read(self, opts):
        sig = self._service._last_signature

        self._value = sig
        print(
            f"[{ts()}][SEC] signature_read: returning {len(self._service._last_signature)} bytes")

        return sig
