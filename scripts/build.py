#!/usr/bin/env python3

import os
import subprocess
import sys

# TODO: remove hardcoded 9810 data, N10L avbfooter
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
rb_count = sys.argv[4] if len(sys.argv) > 4 else None

sign_json = os.path.join(sboot_dir, "sbl1.json")
sboot_path = os.path.join(bl_dir, "sboot.bin")

def sign(image_path, stage, update_header=False):
    cmd = [sys.executable, "scripts/sign.py", image_path, keys_path, stage,]
    if stage == "st1":
        cmd += ["--sbl1-json", sign_json]
    if update_header:
        cmd.append("--update-header")
    if rb_count is not None:
        cmd += ["--rb-count", rb_count]
    subprocess.run(cmd, check=True)

for image in IMAGES_SBOOT:
    sign(os.path.join(sboot_dir, image), stage="st1" if image == "fwbl1.bin" else "st2", update_header=(image == "bl31.bin"))

subprocess.run([sys.executable, "scripts/merge.py", sboot_dir, sboot_path], check=True)

for image in IMAGES_BL:
    sign(os.path.join(bl_dir, image), stage="st2")
