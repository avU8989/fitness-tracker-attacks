from dbus_next.service import (
    ServiceInterface, method, dbus_property, PropertyAccess)

# Source: https://git.kernel.org/pub/scm/bluetooth/bluez.git/tree/doc/org.bluez.Agent.rst


class Agent(ServiceInterface):
    # The peripheral should display a yes no agent for a generated passkey if it matches with the on in the client then ok
    # we dont need request/display pin code as that would be legacy pairing Pin (1-16 chars) and only goes for classic bluetooth (BR/EDR)

    def __init__(self):
        super().__init__("org.bluez.Agent1")

    # AuthorizeService() --> called when a service connection needs auth
    # void AuthorizeService(object device, string uuid)
    @method()
    def AuthorizeService(device: "o", uuid: "s"):
        # We can add policies here like:
        # a trusted list (only trust previously bonded/paired devices),
        # or a whitelist (to block only specific MAC addresses --> for example a MAC address that is not bonded and failed the bonding process multiple times -> could possible be an attacker)
        # we can also log for audits (which MAC Address wanted to request acces to which service )

        # TODO add later a trusted list and a white list, maybe in final ble peripheral with le sc + mitm protection (through numerical passkey) + crp (digital signature with ECDH key)

        print(f"[Agent] Authorizing device: {device} for service: {uuid}")
        return

    @method()
    # Release() --> releasing for unregistering the agent and cleaning up
    def Release():
        print("[Agent] Unregistering agent...")

    @method()
    # void DisplayPasskey(object device, uint32 passkey, uint16 entered)
    def DisplayPasskey(self, device: "o", passkey: "u", entered: "q"):
        """BlueZ calls this to display passkey (Numerical Passkey)"""
        print(
            f"[Agent] Display Passkey for {device} with: {passkey:06d} entered={entered}")

    # void RequestConfirmation(object device, uint32 passkey)
    @method()
    def RequestConfirmation(self, device: "o", passkey: "u"):
        print(
            f"[Agent] Requesting confirmation for device: {device} with passkey: {passkey:06d}")
        # auto accepting
        return

    @method()
    def Cancel(self):
        print("[Agent] Cancelled pairing")
