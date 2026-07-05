#!/usr/bin/env python3

import os
import subprocess
import sys

IMAGES_SBOOT = [
    "bl2.bin",
    "bl31.bin",
    "el3_mon.bin",
    "fwbl1.bin",
    "secure_payload.bin",
    "u-boot.bin"
]

IMAGES_BL = [
    "cm.bin",
    "keystorage.bin",
    "sboot.bin"
]

keys_path = sys.argv[1]
sboot_dir = sys.argv[2]
bl_dir = sys.argv[3]
rb_count = [sys.argv[4]] if len(sys.argv) > 4 else []

sign_json = os.path.join(sboot_dir, "sbl1.json")
sboot_path = os.path.join(bl_dir, "sboot.bin")

for image in IMAGES_SBOOT:
    subprocess.run([sys.executable, "scripts/sign.py", os.path.join(sboot_dir, image), keys_path, sign_json, *rb_count], check=True)

# TODO: N10L avbfooter
subprocess.run([sys.executable,"scripts/merge.py", sboot_dir, sboot_path], check=True)

for image in IMAGES_BL:
    subprocess.run([sys.executable, "scripts/sign.py", os.path.join(bl_dir, image), keys_path, sign_json, *rb_count], check=True)
