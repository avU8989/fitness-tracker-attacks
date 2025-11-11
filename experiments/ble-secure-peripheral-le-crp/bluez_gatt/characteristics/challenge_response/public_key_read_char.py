from bluez_gatt.characteristics.gatt_characteristic import GATTCharacteristicBase
from bluez_gatt.services.secure_service import SecureService
from cryptography.hazmat.primitives import hashes, serialization
from config.security_cfg import DEVICE_PUBLIC_KEY
from utils.common import ts


class PublicKeyCharacteristic(GATTCharacteristicBase):
    def __init__(self, path: str, uuid: str, service: SecureService, flags: list[str]):
        super().__init__(path, uuid, service._path, flags)
        self._service = service

    def on_read(self, opts):
        # SPKI structure defined in https://datatracker.ietf.org/doc/html/rfc5280#section-4.1.1.2
        # An algorithm identifier is defined by the following ASN.1 structure:

        # AlgorithmIdentifier  ::=  SEQUENCE  {
        #    algorithm               OBJECT IDENTIFIER,
        #    parameters              ANY DEFINED BY algorithm OPTIONAL  }

        # DER-encoded Subject Public Key Info (SPKI) for ECDSA P-256 to have the app guard against malicious and malformed DER SPKI formats
        der_bytes = DEVICE_PUBLIC_KEY.public_bytes(
            encoding=serialization.Encoding.DER, format=serialization.PublicFormat.SubjectPublicKeyInfo)

        digest = hashes.Hash(hashes.SHA256())
        digest.update(der_bytes)
        fingerprint = digest.finalize().hex()

        print(f"[{ts()}][SEC] Public key read requested.")
        print(f"[{ts()}][SEC] DER (SPKI) length = {len(der_bytes)} bytes")
        print(f"[{ts()}][SEC] DER preview = {der_bytes[:20].hex()}...")
        print(f"[{ts()}][SEC] Public key SHA256 fingerprint = {fingerprint}")

        self._value = der_bytes

        # expose public key to app, app verifies it with stored fingerprint
        return der_bytes
