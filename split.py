#!/usr/bin/env python3
import os
import sys

SIZES = {
    "fwbl1.bin": 0x2000,
    "bl31.bin": 0x13000,
    "bl2.bin": 0x4F000,
    "pad.bin": 0x19000,
    "u-boot.bin": 0x180000,
    "el3_mon.bin": 0x40000,
    "secure_payload.bin": 0x80000,
    "signerv2.bin": 0x210,
}

sboot = sys.argv[1]
os.makedirs("sboot", exist_ok=True)
with open(sboot, "rb") as f:
    data = f.read()
if len(data) == 0x400000: # N10L
    SIZES["secure_payload.bin"] = 0x100000
    SIZES["avb.bin"] = 0x400000 - (
        sum(SIZES.values())
    )
offset = 0
for name, size in SIZES.items():
    with open(os.path.join("sboot", name), "wb") as f:
        f.write(data[offset:offset + size])
    offset += size