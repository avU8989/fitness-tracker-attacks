from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.asymmetric.ec import EllipticCurvePrivateKey
from cryptography.hazmat.primitives import serialization
import pathlib


# NIST P-256 curve order constant (used for low-S normalization)
N_P256 = int(
    "FFFFFFFF00000000FFFFFFFFFFFFFFFFBCE6FAADA7179E84F3B9CAC2FC632551", 16)

# File where the device key will be stored
KEY_PATH = pathlib.Path("ble-secure-peripheral-le-crp/device_key.pem")


def createPrivateKey():
    """Create a new """
    private_key = ec.generate_private_key(ec.SECP256R1())
    return private_key


def storePrivateKey(private_key: EllipticCurvePrivateKey):
    # allow serialization of key to bytes (encoding pem or der format)
    pem_bytes = private_key.private_bytes(
        encoding=serialization.Encoding.PEM, format=serialization.PrivateFormat.PKCS8, encryption_algorithm=serialization.NoEncryption())

    KEY_PATH.parent.mkdir(parents=True, exist_ok=True)
    KEY_PATH.write_bytes(pem_bytes)


def loadPrivateKey():
    if KEY_PATH.exists():
        # load the private key from the path
        private_key = serialization.load_pem_private_key(
            KEY_PATH.read_bytes(), password=None
        )
    else:
        private_key = createPrivateKey()
        storePrivateKey(private_key)

    return private_key


# Constants to be used in the challenge response characteristics
DEVICE_PRIVATE_KEY = loadPrivateKey()
DEVICE_PUBLIC_KEY = DEVICE_PRIVATE_KEY.public_key()
