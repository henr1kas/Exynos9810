#!/usr/bin/env python3

import os
import sys
from s5e9810 import soc_data

sboot_size = os.path.getsize(sys.argv[2])
soc = soc_data(sboot_size)

out = bytearray()
for image in soc.sboot:
    with open(os.path.join(sys.argv[1], image.name), "rb") as f:
        out.extend(f.read())

with open(sys.argv[2], "wb") as f:
    f.write(out)
