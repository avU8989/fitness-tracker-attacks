import subprocess


def setup_btmgmt():
    """
    Configure Bluetooth adapter for BLE-only mode, advertising, bonding using btmgmt    """

    cmds = [
        ["btmgmt", "power", "off"],
        ["btmgmt", "bredr", "off"],
        ["btmgmt", "le", "on"],
        ["btmgmt", "connectable", "on"],
        ["btmgmt", "advertising", "on"],
        ["btmgmt", "bondable", "on"],
        ["btmgmt", "discov", "yes"],

        # https://www.bluetooth.com/blog/bluetooth-technology-protecting-your-privacy/
        # enables privacy support on a Bluetooth device using the BlueZ stack, which causes the device to start using Random Private Addresses (RPAs)
        # for its Bluetooth address to enhance user privacy.
        ["btmgmt", "privacy", "on"],  # enables random resolvable addresses

        ["btmgmt", "power", "on"],
    ]

    for cmd in cmds:
        try:
            print(f"→ Running: {' '.join(cmd)}")
            subprocess.run(["sudo"] + cmd, check=True, text=True)
        except subprocess.CalledProcessError as e:
            print(e)
            return False

    print("Bluetooth adapter configured successfully.")

    return True
