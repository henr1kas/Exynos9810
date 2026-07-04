#!/usr/bin/env python3

import subprocess
import sys
from pathlib import Path

IMAGES_SBOOT = [
    "bl2.bin",
    "bl31.bin",
    "el3_mon.bin",
    "fwbl1.bin",
    "secure_payload.bin",
    "u-boot.bin",
]

IMAGES_BL = [
    "cm.bin",
    "keystorage.bin",
    "sboot.bin"
]

sign_json = Path(sys.argv[2]) / "sbl1.json"
keys_path = Path(sys.argv[1])
sboot_path = Path(sys.argv[3]) / "sboot.bin"
rb_count = [sys.argv[4]] if len(sys.argv) > 4 else []

for image in IMAGES_SBOOT:
    image_path = Path(sys.argv[2]) / image
    subprocess.run([sys.executable, "scripts/sign.py", str(image_path), str(keys_path), str(sign_json), *rb_count], check=True)

# TODO: N10L avbfooter
subprocess.run([sys.executable, "scripts/merge.py",  str(Path(sys.argv[2])), str(sboot_path)], check=True)

for image in IMAGES_BL:
    image_path = Path(sys.argv[3]) / image
    subprocess.run([sys.executable, "scripts/sign.py", str(image_path), str(keys_path), str(sign_json), *rb_count], check=True)
