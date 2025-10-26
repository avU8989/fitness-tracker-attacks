import subprocess


def setup_btmgmt(adapter: str = "hci0"):
    """
    Configure Bluetooth adapter for BLE-only mode, advertising, bonding using btmgmt    """

    cmds = [
        ["btmgmt", "-i", adapter, "power", "off"],
        ["btmgmt", "-i", adapter, "bredr", "off"],
        ["btmgmt", "-i", adapter, "connectable", "on"],
        ["btmgmt", "-i", adapter, "advertising", "on"],
        ["btmgmt", "-i", adapter, "bondable", "on"],
        # the attacker uses static mac address
        ["btmgmt", "-i", adapter, "privacy", "off"],
        ["btmgmt", "-i", adapter, "discov", "yes"],
        ["btmgmt", "-i", adapter, "power", "on"],
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
