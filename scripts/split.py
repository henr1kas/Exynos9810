#!/usr/bin/env python3

import ctypes
import json
from datetime import datetime, timezone
import os
import sys
from sbl1 import SBL1

def bcd_nibbles_to_int(value, start_nibble, num_digits):
    result = 0
    for i in range(num_digits):
        shift = 4 * (start_nibble + num_digits - 1 - i)
        nibble = (value >> shift) & 0xF
        result = result * 10 + nibble
    return result

def bcd_to_int(b):
    return ((b >> 4) * 10) + (b & 0xF)

def parse_bcd_timestamp(val):
    year = bcd_to_int((val >> 24) & 0xFF) + 2000
    month = bcd_to_int((val >> 16) & 0xFF)
    day = bcd_to_int((val >> 8) & 0xFF)
    hour = bcd_to_int(val & 0xFF)
    dt = datetime(year, month, day, hour, tzinfo=timezone.utc)
    return int(dt.timestamp())

def struct_to_dict(s):
    out = {}
    for name, ctype in s._fields_:
        if name == "image":
            continue
        val = getattr(s, name)
        if name == "soc_info":
            v = int.from_bytes(bytes(val[0:4]), "little")
            out["evt"] = bcd_nibbles_to_int(v, 0, 1)
            out["soc"] = bcd_nibbles_to_int(v, 1, 4)
            out["timestamp"] = parse_bcd_timestamp(int.from_bytes(bytes(val[4:8]), "little"))
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
