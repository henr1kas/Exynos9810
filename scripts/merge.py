#!/usr/bin/env python3

import os
import sys

FILES = [
    "fwbl1.bin",
    "bl31.bin",
    "bl2.bin",
    "pad.bin",
    "u-boot.bin",
    "el3_mon.bin",
    "secure_payload.bin",
    "signerv2.bin",
    "avb.bin" # only n10lite
]

out = bytearray()
for name in FILES:
    path = os.path.join(sys.argv[1], name)
    if os.path.exists(path):
        with open(path, "rb") as f:
            out.extend(f.read())
with open(sys.argv[2], "wb") as f:
    f.write(out)
