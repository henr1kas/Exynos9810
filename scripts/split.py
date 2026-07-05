#!/usr/bin/env python3

import json
import os
import sys
from sbl1 import SBL1, sbl1_to_dict

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

if __name__ == "__main__":
    os.makedirs(sys.argv[2], exist_ok=True)
    with open(sys.argv[1], "rb") as f:
        data = f.read()
    if len(data) == 0x400000: # N10L
        SIZES["secure_payload.bin"] = 0x100000
        SIZES["avb.bin"] = 0x400000 - (
            sum(SIZES.values())
        )
    offset = 0
    for name, size in SIZES.items():
        with open(os.path.join(sys.argv[2], name), "wb") as f:
            f.write(data[offset:offset + size])
        offset += size
    with open(os.path.join(sys.argv[2], "sbl1.json"), "w", newline="\n") as f:
        json.dump(sbl1_to_dict(SBL1.from_buffer_copy(data[0:0x2000])), f, indent=2)
