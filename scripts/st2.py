#!/usr/bin/env python3

import ctypes

class ST2(ctypes.LittleEndianStructure):
    _pack_ = 1
    _fields_ = [
        ("rb_count",  ctypes.c_uint32),
        ("sign_type", ctypes.c_uint32),
        ("key_type",  ctypes.c_uint32),
        ("key_index", ctypes.c_uint32),
        ("signature", ctypes.c_uint8 * 0x100),
    ]
