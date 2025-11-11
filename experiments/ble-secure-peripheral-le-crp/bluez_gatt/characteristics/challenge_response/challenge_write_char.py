from bluez_gatt.characteristics.gatt_characteristic import GATTCharacteristicBase
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import hashes
import base64
from cryptography.hazmat.primitives.asymmetric.utils import decode_dss_signature
from config.security_cfg import DEVICE_PRIVATE_KEY, N_P256
from bluez_gatt.services.secure_service import SecureService


class ChallengeCharacteristic(GATTCharacteristicBase):
    def __init__(self, path: str, uuid: str, service: SecureService, flags: list[str]):
        super().__init__(path, uuid, service._path, flags)
        self._service = service

    def on_write(self, value: bytes, opts: dict):
        print(f"[DEBUG] on_write called! value={value.hex()}")
        # value = random nonce from app
        # the device computes a digital signature over the nonce using ECDSA with SHA-256
        # SHA-256 hashes the nonce, and that hash is signed using the devices private key
        signature = DEVICE_PRIVATE_KEY.sign(value, ec.ECDSA(hashes.SHA256()))

        # we use raw R∥S (R concatenated with S --> concatenated integers) signature, because we can define the length and for ble payloads the transfer is simpler
        # its easier to base64 and encode and transfer, the app just splits into two 32-bytes halves for verification
        # R∥S signature is not standarized --> the standard is DER its the default output format and standardized ASN, but it uses variable length --> so not so optimal for our BLE transfer
        r, s = decode_dss_signature(signature)
        # --- low-S normalization ---
        if s > N_P256 // 2:
            s = N_P256 - s
        raw_sig = r.to_bytes(32, "big") + s.to_bytes(32, "big")
        self._service._last_signature = raw_sig
        self._service._last_challenge = value

        self._value = value

        print(
            f"[SEC] Signature ready, base64={base64.b64encode(raw_sig).decode()}")
