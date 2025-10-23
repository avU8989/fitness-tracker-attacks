1 — Security goals (what “hardened” must achieve)

Prevent unauthenticated peripherals from delivering sensitive plaintext data.

Prevent app from blindly trusting cached GATT / name/UUID or a reconnect without re-establishing authenticated session.

Detect and block BLESA-style resumption attacks (client reconnects when LTK missing).

Provide layered defense: link-layer (LTK) and application-layer auth (HMAC/challenge).

Provide auditability: logs (btmon + device/app logs) to prove defenses.

