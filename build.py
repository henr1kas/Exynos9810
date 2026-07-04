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
    subprocess.run([sys.executable, "sign.py", image, sys.argv[1]], check=True)

# TODO: N10L avbfooter
subprocess.run([sys.executable, "scripts/merge.py",  sys.argv[2], sys.argv[3]], check=True)
subprocess.run([sys.executable, "sign.py", sys.argv[3], sys.argv[1]], check=True)
