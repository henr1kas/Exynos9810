#!/usr/bin/env python3

import os
import subprocess
import sys

from s5e9810 import soc_data

keys_path = sys.argv[1]
sboot_dir = sys.argv[2]
bl_dir = sys.argv[3]
rb_count = sys.argv[4] if len(sys.argv) > 4 else None

sign_json = os.path.join(sboot_dir, "sbl1.json")
sboot_path = os.path.join(bl_dir, "sboot.bin")

soc = soc_data(os.path.getsize(sboot_path))

def sign(image_path, stage, update_header=False):
    cmd = [sys.executable, "scripts/sign.py", image_path, keys_path, stage,]
    if stage == "st1":
        cmd += ["--sbl1-json", sign_json]
    if update_header:
        cmd.append("--update-header")
    if rb_count is not None:
        cmd += ["--rb-count", rb_count]
    subprocess.run(cmd, check=True)

for image in soc.sboot:
    if image.stage is None:
        continue
    sign(os.path.join(sboot_dir, image.name), stage=image.stage, update_header=image.update_header,)

subprocess.run([sys.executable, "scripts/merge.py", sboot_dir, sboot_path], check=True)

for image in soc.bl:
    if image.stage is None:
        continue
    sign(os.path.join(bl_dir, image.name), stage=image.stage, update_header=image.update_header,)
