# <Attack  — Title>
# Attack x (Notes for Attack) #

## Goal ## 
Describe the vulnerability and how an attacker might exploit it

## Threat Model Mapping — STRIDE

| STRIDE Category | Entry Point(s) | Description | Potential Impact |  Mitigations |
|-----------------|----------------|--------------|------------------|------------------------|
| **Spoofing** | 
| **Tampering** |
| **Repudiation** | 
| **Information discolsure** | 
| **Denial of service** | 
| **Elevation of privilege** | 

---

## Precondition ## 
 Preconditions for attack scenario and for the attack script to work
 - e.g. "fitness-tracker" app will connect automatically to devices based on visible identifiers (device name, mac address)

## Procedure ##
 Attack Scenario describing the steps on how the attacker would go against our system e.g. : 

**1.** Static MAC Addresses used and identified by attacker

**2.** Attacker will run fake peripheral

**3.** App connects to fake peripheral due to faulty connection logic

## Captured Data ##  
  Describes the Captured Data we receive from our logs (can be on backend layer, app layer or peripheral layer)

## Success Criteria ##
 Quantitative threshold, e.g. 95 % forged health metrics will appear in backend

## Mitigation Under Test ##
What you enable in the hardened run (e.g., LE Secure Connections + application-layer signatures).

## Metrics ##  
Acceptance rate (%), detection rate (%), etc

## How to run the Attack ##
Steps on how to run the attack script

## Notes / Safety ##

Notes for implementing the attack e.g. problems during implementation, preconditions noted to run the attack succesfully, research papers about vulnerabilties regarding the attack
