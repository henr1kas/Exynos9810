#!/usr/bin/env python3

import subprocess
import sys

IMAGES = [
    "sboot/bl2.bin",
    "sboot/bl31.bin",
    "sboot/el3_mon.bin",
    "sboot/fwbl1.bin",
    "sboot/secure_payload.bin",
    "sboot/u-boot.bin",

    "bl/cm.bin",
    "bl/keystorage.bin"
]

for image in IMAGES:
    subprocess.run([sys.executable, "sign.py", image, "keys"], check=True)

# TODO: N10L avbfooter
subprocess.run([sys.executable, "merge.py", "sboot"], check=True)
subprocess.run([sys.executable, "sign.py", "bl/sboot.bin", "keys"], check=True)
