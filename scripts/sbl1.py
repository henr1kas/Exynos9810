#!/usr/bin/env python3

import ctypes

class SBL1(ctypes.LittleEndianStructure):
    _pack_ = 1
    _fields_ = [
        # Header
        ("num_of_sector",      ctypes.c_uint32),
        ("checksum",           ctypes.c_uint32),
        ("en_addr",            ctypes.c_uint32),
        ("en_size",            ctypes.c_uint32),
        # BL1
        ("image",              ctypes.c_uint8 * 7144),
        # BL1 info
        ("soc_info",           ctypes.c_uint8 * 8),
        # SignerVer04
        ("codesigner_version", ctypes.c_uint32),
        ("ap_info",            ctypes.c_char * 4),
        ("time",               ctypes.c_uint64),
        ("rb_count",           ctypes.c_uint32),
        ("signing_type",       ctypes.c_uint32),
        ("debug_certificate",  ctypes.c_uint8 * 0x1C),
        ("key_index",          ctypes.c_uint32),
        ("st2_publickey",      ctypes.c_uint8 * 0x10C),
        ("func_ptr",           ctypes.c_uint8 * 0x80),
        ("minor_id",           ctypes.c_uint16),
        ("major_id",           ctypes.c_uint16),
        ("reserved",           ctypes.c_uint8 * 0x8),
        ("st1_publickey",      ctypes.c_uint8 * 0x10C),
        ("hmac",               ctypes.c_uint8 * 0x20),
        ("signature_size",     ctypes.c_uint32),
        ("signature",          ctypes.c_uint8 * 0x100),
    ]
