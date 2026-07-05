#!/usr/bin/env python3

import ctypes
import json
from datetime import datetime, timezone
import os
import sys
from sbl1 import SBL1

def struct_to_dict(s):
    out = {}
    for name, ctype in s._fields_:
        if name == "image":
            continue
        val = getattr(s, name)
        if name == "soc_info":
            v = int.from_bytes(bytes(val[0:4]), "little")
            t = int.from_bytes(bytes(val[4:8]), "little")
            hex_str = f"{v:x}"
            evt_str = hex_str[4:]
            if len(evt_str) == 4:
                evt_str = f"{int(evt_str[:2], 16)}.{int(evt_str[2:], 16)}"
            out["evt"] = evt_str
            out["soc"] = int(hex_str[:4])
            h = f"{t:08x}"
            dt = datetime(year=2000 + int(h[0:2]), month=int(h[2:4]), day=int(h[4:6]), hour=int(h[6:8]), tzinfo=timezone.utc)
            out["timestamp"] = int(dt.timestamp())
        elif isinstance(val, ctypes.Array):
            out[name] = bytes(val).hex()
        elif isinstance(val, bytes):
            out[name] = val.decode() if name == "ap_info" else val.hex()
        else:
            out[name] = val
    return out

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
        json.dump(struct_to_dict(SBL1.from_buffer_copy(data[0:0x2000])), f, indent=2)
