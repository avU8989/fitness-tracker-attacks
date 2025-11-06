1 — Security goals (what “hardened” must achieve)

Prevent unauthenticated peripherals from delivering sensitive plaintext data.

Prevent app from blindly trusting cached GATT / name/UUID or a reconnect without re-establishing authenticated session.

Detect and block BLESA-style resumption attacks (client reconnects when LTK missing).

Provide layered defense: link-layer (LTK) and application-layer auth (HMAC/challenge).

Provide auditability: logs (btmon + device/app logs) to prove defenses.

This version includes mitigation techniques like 
- LE Secure Connection
- Pairing Method: Numeric Comparison
- RPA 



To run this peripheral 

I have the problem of setting up the hci1 adapter with a script through python because it always sets it to the hci0 adapter, so for the real peripheral we need to set the btmgmt settings ourselves

go to `sudo btmgmt`

select the right index -> my index 1 will be my hci1 -- my hci1 is my bluetooth toggle 

``` bash
Index list with 2 items

hci1:	Primary controller
	addr A0:AD:9F:6F:2F:D1 version 13 manufacturer 93 class 0x60010c
	supported settings: powered connectable fast-connectable discoverable bondable link-security ssp br/edr le advertising secure-conn debug-keys privacy static-addr phy-configuration cis-central cis-peripheral 
	current settings: powered connectable discoverable bondable ssp br/edr le secure-conn cis-central cis-peripheral 
	name FitTrack
	short name 
hci0:	Primary controller
	addr [REDACTED] version 10 manufacturer 93 class 0x000000
	supported settings: powered connectable fast-connectable discoverable bondable link-security ssp br/edr le advertising secure-conn debug-keys privacy static-addr phy-configuration wide-band-speech 
	current settings: powered connectable discoverable bondable le advertising 
	name FitTrack
	short name 
avu@avu-Lenovo-V15-G4-ABP:~/fitness-tracker-attacks/experiments/A1-BLE-Injection/attack-1/attacker-peripheral$ sudo btmgmt
[mgmt]# select 1
Selected index 1

```

in the mgmt make sure you run 
``` bash
    power off
    bredr off # classic bluetooth off
    le on # low energy
    sc on # secure connection
    advertising on # advertises your peripheral
	connectable on # connectable should be first called before you set the discov setting on yes
    discov yes # to be able to scan your peripheral
    bondable yes # for pairing

```
