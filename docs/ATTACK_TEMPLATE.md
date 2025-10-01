# <Ax — Title>

**Goal**  
One-sentence objective, e.g., “Assess whether the app accepts forged heart-rate values from a non-paired peripheral.”

**Threat Model Mapping**  
STRIDE: <Spoofing/Tampering/...> · Entry point(s): <BLE GATT / App pipeline / API>.

**Assumptions & Preconditions**  
- Testbed devices, synthetic data, legal authorization.
- Feature flags/config state (e.g., bonding disabled in baseline).

**Setup (High Level)**  
- Prepare the app and backend in a test environment.
- Use a BLE tooling setup to emulate a peripheral and send controlled notifications.  
  _Note: Do not include low-level exploit steps or third-party secrets._

**Procedure (High Level)**  
1) Start app and subscribe to the target characteristic.  
2) Generate a controlled sequence of metrics (e.g., 60–200 bpm at 1–5 Hz).  
3) Observe app parsing → upload → backend ingestion.  
4) Record timestamps and identifiers.

**Captured Data**  
- Raw app receive time, payload, sequence/timestamp.  
- Backend accept/reject outcome and response codes.

**Success Criteria**  
Quantitative threshold, e.g., “≥95% of forged values appear in backend within 2 s median latency.”

**Mitigation Under Test**  
What you enable in the hardened run (e.g., LE Secure Connections + application-layer signatures).

**Metrics Reported**  
Acceptance rate (%), detection rate (%), false positives (%), E2E latency (ms, median/p95), overhead.

**Cleanup**  
Return app/backend to baseline, rotate test tokens/keys if used.

**Notes / Safety**  
This document omits actionable exploit details. Use only in authorized environments.
