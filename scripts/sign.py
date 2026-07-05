#!/usr/bin/env python3

import argparse
import hashlib
import hmac
import os
import struct
import time
import ctypes
import json
from datetime import datetime, timezone

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa

from sbl1 import SBL1
from st2 import ST2

RSA_MOD_SIZE = 0x100
RSA_EXP_SIZE = 0x4

def load_private_key(path):
    with open(path, "rb") as f:
        pem = f.read()
    key = serialization.load_pem_private_key(pem, password=None)
    if not isinstance(key, rsa.RSAPrivateKey) or key.key_size != RSA_MOD_SIZE * 8:
        raise ValueError(f"Expected RSA-{RSA_MOD_SIZE * 8} private key: {path}")
    return key

def pubkey_blob(pub):
    n = pub.public_numbers()
    return struct.pack(
        f"<I{RSA_MOD_SIZE}sI{RSA_EXP_SIZE}s",
        RSA_MOD_SIZE, n.n.to_bytes(RSA_MOD_SIZE, "little"),
        RSA_EXP_SIZE, n.e.to_bytes(RSA_EXP_SIZE, "little"),
    )

def sign_pss(key, data):
    return key.sign(data, padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=0x20), hashes.SHA256())[::-1]

def header_digest(data):
    return hashlib.sha256(data[0x10:]).digest()[:4]

def int_to_bcd(v):
    return ((v // 10) << 4) | (v % 10)
 
def int_to_bcd_nibbles(value, start_nibble, num_digits):
    v = 0
    tmp = value
    for i in range(num_digits):
        digit = tmp % 10
        tmp //= 10
        v |= (digit & 0xF) << (4 * (start_nibble + i))
    return v
 
def build_soc_info(evt, soc, timestamp):
    word = int_to_bcd_nibbles(evt, 0, 1) | int_to_bcd_nibbles(soc, 1, 4)
    dt = datetime.fromtimestamp(timestamp, tz=timezone.utc)
    ts_val = (
        (int_to_bcd(dt.year - 2000) << 24)
        | (int_to_bcd(dt.month) << 16)
        | (int_to_bcd(dt.day) << 8)
        | int_to_bcd(dt.hour)
    )
    return word.to_bytes(4, "little") + ts_val.to_bytes(4, "little")

def load_json_into_struct(sbl1, j):
    if all(k in j for k in ("evt", "soc", "timestamp")):
        sbl1.soc_info[:] = build_soc_info(j["evt"], j["soc"], j["timestamp"])
 
    for name, ctype in sbl1._fields_:
        if name in ("image", "soc_info") or name not in j:
            continue
        val = j[name]
        if name == "ap_info":
            sbl1.ap_info = val.encode()
            continue
        cur = getattr(sbl1, name)
        if isinstance(cur, ctypes.Array):
            cur[:] = bytes.fromhex(val)
        else:
            setattr(sbl1, name, val)

def sign_st1(data, st1_privatekey, st2_publickey, hmac_key, rb_count, json_path):
    if len(data) != ctypes.sizeof(SBL1):
        raise ValueError(f"fwbl1.bin must be 0x{ctypes.sizeof(SBL1):X} bytes")
 
    sbl1 = SBL1.from_buffer(data)
    with open(json_path) as f:
        j = json.load(f)
    load_json_into_struct(sbl1, j)
 
    st1_publickey = pubkey_blob(st1_privatekey.public_key())
    sbl1.checksum = 0
    sbl1.time = int(time.time())
    if rb_count is not None:
        sbl1.rb_count = rb_count
    sbl1.st2_publickey[:] = st2_publickey
    sbl1.st1_publickey[:] = st1_publickey
    sbl1.hmac[:] = hmac.digest(hmac_key, st1_publickey, "sha256")
    sbl1.signature[:] = sign_pss(st1_privatekey, memoryview(data)[:SBL1.st1_publickey.offset])
    sbl1.checksum = int.from_bytes(header_digest(data), "little")
    return data

def sign_st2(data, st2_privatekey, rb_count, update_header):
    if update_header:
        data[4:8] = bytes(4)
    footer = ST2.from_buffer(memoryview(data)[len(data) - ctypes.sizeof(ST2):])
    if rb_count is not None:
        footer.rb_count = rb_count
    footer.signature[:] = sign_pss(st2_privatekey, memoryview(data)[:len(data) - 0x100])
    if update_header:
        data[4:8] = header_digest(data)
    return data

if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Exynos CodeSigner comaptible v4, RSA-PSS")
    ap.add_argument("input_file", help="Path to the image to sign")
    ap.add_argument("keys_dir",  help="Directory containing the signing keys")
    ap.add_argument("sbl1_json", help="sbl1.json file containing BL1 sig info")
    ap.add_argument("rb_count", nargs="?", default=None, type=int, help="Override rb_count of images")
    args = ap.parse_args()

    st1_privatekey = load_private_key(os.path.join(args.keys_dir, "st1.pem"))
    st2_privatekey = load_private_key(os.path.join(args.keys_dir, "st2.pem"))
    with open(os.path.join(args.keys_dir, "hmac.bin"), "rb") as f:
        hmac_key = f.read()

    with open(args.input_file, "rb") as f:
        size = os.fstat(f.fileno()).st_size
        data = bytearray(size)
        f.readinto(data)

    name = os.path.basename(args.input_file)
    if name == "fwbl1.bin":
        signed = sign_st1(data, st1_privatekey, pubkey_blob(st2_privatekey.public_key()), hmac_key, args.rb_count, args.sbl1_json)
    else:
        signed = sign_st2(data, st2_privatekey, args.rb_count, name == "bl31.bin")
    with open(args.input_file, "wb") as f:
        f.write(signed)
