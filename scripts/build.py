#!/usr/bin/env python3
import os
import subprocess
import sys
import importlib

soc_name = sys.argv[1]
keys_path = sys.argv[2]
work_dir = sys.argv[3]
rb_count = sys.argv[4] if len(sys.argv) > 4 else None

soc_module = importlib.import_module(soc_name)
soc = soc_module.soc_data()

def sign(image_path, stage, update_header=False, ree=False, sbl1_json=None, signing_type=0, avb_name="", avb_size=0):
    cmd = [sys.executable, "scripts/sign.py", image_path, keys_path, stage]
    if stage == "st1":
        if os.path.exists(sbl1_json):
            cmd += ["--sbl1-json", sbl1_json]
    if update_header:
        cmd.append("--update-header")
    if ree:
        cmd += ["--st2-key-type", "1"]
    if rb_count is not None:
        cmd += ["--rb-count", rb_count]
    cmd += ["--signing-type", str(signing_type)]
    cmd += ["--avb-partition-name", avb_name]
    cmd += ["--avb-partition-size", str(avb_size)]
    subprocess.run(cmd, check=True)

def merge(paths, out_path):
    out = bytearray()
    for path in paths:
        with open(path, "rb") as f:
            out.extend(f.read())
    with open(out_path, "wb") as f:
        f.write(out)

for image in soc.odin:
    if image.split:
        subdir = os.path.join(work_dir, os.path.splitext(image.name)[0])
        sbl1_json = os.path.join(subdir, "sbl1.json")

        for inner in image.split:
            if inner.stage is None:
                continue
            sign(
                os.path.join(subdir, inner.name),
                stage=inner.stage,
                update_header=inner.update_header,
                ree=inner.ree,
                avb_name=inner.avb,
                avb_size=inner.size,
                sbl1_json=sbl1_json,
                signing_type=soc.signing_type
            )

        merge(
            [os.path.join(subdir, inner.name) for inner in image.split],
            os.path.join(work_dir, image.name),
        )

    if image.stage is not None:
        sign(
            os.path.join(work_dir, image.name),
            stage=image.stage,
            update_header=image.update_header,
            ree=image.ree,
            avb_name=image.avb,
            avb_size=image.size,
            signing_type=soc.signing_type
        )