#!/usr/bin/env python3

import json
import os
import sys
from sbl1 import SBL1, sbl1_to_dict
from s5e9810 import soc_data

if __name__ == "__main__":
    os.makedirs(sys.argv[2], exist_ok=True)

    with open(sys.argv[1], "rb") as f:
        data = f.read()

    soc = soc_data(len(data))

    offset = 0
    bl1_start = 0
    bl1_end = 0
    for image in soc.sboot:
        with open(os.path.join(sys.argv[2], image.name), "wb") as f:
            f.write(data[offset:offset + image.size])
        if image.stage == "st1":
            bl1_start = offset
            bl1_end = image.size
        offset += image.size

    with open(os.path.join(sys.argv[2], "sbl1.json"), "w", newline="\n") as f:
        json.dump(sbl1_to_dict(SBL1.from_buffer_copy(data[bl1_start:bl1_end])), f, indent=2)
