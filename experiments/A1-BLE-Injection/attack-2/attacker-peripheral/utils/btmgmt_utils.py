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
