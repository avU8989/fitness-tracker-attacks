from bluez_peripheral.gatt.service import Service
from bluez_peripheral.gatt.characteristic import characteristic, CharacteristicFlags as CF
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric.utils import decode_dss_signature
import base64
import time
# https: // www.radwin.org/michael/projects/jnfs/paper/node32.html
# To guard against spoofing and MITM we are adding a challenge response protocol with a digital signature for verifying real peripheral
# Initialization --> the user tells the server it needs to be authenticated
# Challenge --> App -> Peripheral --> write random nonce on CHALLENGE_CHAR --> app generates 16-32 random bytes
# Response --> Peripheral -> App --> Read from SIGN_CHAR --> peripheral signs the nonce with its private key and stores the nonce under last_signature/last_challenge
# Verfication --> App --> app verifies signature using stored fingerprint

# Why we choose Digital Signature over HMAC
# HMAC secret key --> both know it while in digital signature only peripheral knows the private key
# While on HMAC the device secret can be leaked, digital signature will only leak the device public key

# BLE has two layers of security
# Link Layer Security --> Pairing -> Bonding -> Encryption (LTK, IRK, CSRK) --> protects payload (encrytpion), prevents eavesdropping, MITM --> is managed by OS (BlueZ)
# Application Layer Securtiy --> Challenge-Response (HMAC or Digital Signature) --> prove that the peer is the real trusted device --> implemented in app and in peripheral

CHALLENGE_CHAR = "0000c001-0000-1000-8000-00805f9b34fb"
SECURE_SERVICE = "0000c000-0000-1000-8000-00805f9b34fb"
SIGN_CHAR = "0000c002-0000-1000-8000-00805f9b34fb"
PUBLIC_KEY_CHAR = "0000c003-0000-1000-8000-00805f9b34fb"

# generate or load devices private key aligning with the NIST P-256 eliptic curve scheme standardized by the National Institute of Standards
# it uses ECDSA (Elliptic Curve Digital Signature Alogrithm), which is a signature scheme that use the mathematical properties of eliptic curve to generate and verify digital signatures
# instead of
# DEVICE_PRIVATE_KEY = rsa.generate_private_key(public_exponent=65537, key_size=2048, backend=default_backend())
# we use ec.SECP256R1() it gives the same security, but with tiny keys and signatures --> good for our BLE device where bandwith and CPU is limited
# reasons for EC --> smaller payloads, faster signing/verifying, supported in most crypto libraries and Bluetooth secure connections (also uses P-256) internally
# https://csrc.nist.rip/external/nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-121r2.pdf
# "Low energy Secure Connections security introduced in Bluetooth 4.2 improves low energy security
# through the addition of ECDH public key cryptography(using the P-256 Elliptic Curve) for
# protection against passive eavesdropping and MITM during pairing"

# Digital signature --> private key only known to signer
# Public key --> shared with others
# sign the senders private key
# verified by using the public key
# https://cryptobook.nakov.com/digital-signatures/ecdsa-sign-verify-messages
DEVICE_PRIVATE_KEY = ec.generate_private_key(ec.SECP256R1())

# get public key
DEVICE_PUBLIC_KEY = DEVICE_PRIVATE_KEY.public_key()
N_P256 = int(
    "FFFFFFFF00000000FFFFFFFFFFFFFFFFBCE6FAADA7179E84F3B9CAC2FC632551", 16)


def ts(): return time.strftime("%H:%M:%S") + \
    f".{int(time.time()*1000) % 1000:03d}"


class SecuredService(Service):
    def __init__(self):
        super().__init__(SECURE_SERVICE, True)
        self._last_signature = b""
        self._last_challenge = b""

    @characteristic(CHALLENGE_CHAR, flags=CF.WRITE | CF.ENCRYPT_AUTHENTICATED_WRITE)
    def challenge(self, opts):
        # this is a dummy placeholder — required before adding .setter
        pass

    # https://cryptography.io/en/latest/hazmat/primitives/asymmetric/ec/#cryptography.hazmat.primitives.asymmetric.ec.generate_private_key
    @challenge.setter
    def challenge_write(self, value: bytes, opts):
        print(f"[DEBUG] challenge_write called! value={value.hex()}")
        # value = random nonce from app
        # the device computes a digital signature over the nonce using ECDSA with SHA-256
        # SHA-256 hashes the nonce, and that hash is signed using the devices private key
        signature = DEVICE_PRIVATE_KEY.sign(value, ec.ECDSA(hashes.SHA256()))

        # we use raw R∥S (R concatenated with S --> concatenated integers) signature, because we can define the length and for ble payloads the transfer is simpler
        # its easier to base64 and encode and transfer, the app just splits into two 32-bytes halves for verification
        # R∥S signature is not standarized --> the standard is DER its the default output format and standardized ASN, but it uses variable length --> so not so optimal for out BLE transfer
        r, s = decode_dss_signature(signature)
        # --- low-S normalization ---
        if s > N_P256 // 2:
            s = N_P256 - s
        raw_sig = r.to_bytes(32, "big") + s.to_bytes(32, "big")
        self._last_signature = raw_sig
        self._last_challenge = value
        print(f"[{ts()}][SEC] Signature R={r:064x}")
        print(f"[{ts()}][SEC] Signature S={s:064x}")
        print(f"[{ts()}][SEC] Raw (r||s)={raw_sig.hex()}")
        print(f"[{ts()}][SEC] Base64 signature={base64.b64encode(raw_sig).decode()}")
        return True

    @characteristic(SIGN_CHAR, flags=CF.READ | CF.ENCRYPT_AUTHENTICATED_READ)
    def signature_read(self, opts):
        # central read this characteristic to obtain the latest signature
        print(
            f"[{ts()}][SEC] signature_read: returning {len(self._last_signature)} bytes")

        return self._last_signature

    # SPKI structure defined in https://datatracker.ietf.org/doc/html/rfc5280#section-4.1.1.2
    # An algorithm identifier is defined by the following ASN.1 structure:

    # AlgorithmIdentifier  ::=  SEQUENCE  {
    #    algorithm               OBJECT IDENTIFIER,
    #    parameters              ANY DEFINED BY algorithm OPTIONAL  }

    @characteristic(PUBLIC_KEY_CHAR, flags=CF.READ | CF.ENCRYPT_AUTHENTICATED_READ)
    def public_key_read(self, opts):
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

        # expose public key to app, app verifies it with stored fingerprint
        return der_bytes
