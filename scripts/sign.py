#!/usr/bin/env python3

import argparse
import hashlib
import hmac
import struct
import time
from pathlib import Path
import ctypes
import json
from datetime import datetime, timezone

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa

from sbl1 import SBL1

RSA_SIG_SIZE = 0x100
RSA_MOD_SIZE = 0x100
RSA_EXP_SIZE = 0x4

def load_private_key(path):
    key = serialization.load_pem_private_key(Path(path).read_bytes(), password=None)
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

def sign_fwbl1(data, json_path, st1_privatekey, st2_publickey, hmac_key):
    if len(data) != ctypes.sizeof(SBL1):
        raise ValueError(f"fwbl1.bin must be 0x{ctypes.sizeof(SBL1):X} bytes")
 
    sbl1 = SBL1.from_buffer_copy(data) # will only keep image field from fwbl1.bin, rest from json
    j = json.loads(Path(json_path).read_text())
    load_json_into_struct(sbl1, j)
 
    st1_publickey = pubkey_blob(st1_privatekey.public_key())
    sbl1.checksum = 0
    sbl1.time = int(time.time())
    sbl1.st2_publickey[:] = st2_publickey
    sbl1.st1_publickey[:] = st1_publickey
    sbl1.hmac[:] = hmac.digest(hmac_key, st1_publickey, "sha256")
    sbl1.signature[:] = sign_pss(st1_privatekey, bytes(sbl1)[:SBL1.st1_publickey.offset])
    sbl1.checksum = int.from_bytes(header_digest(bytes(sbl1)), "little")
    return bytes(sbl1)

def sign_compact(name, data, stage2_key):
    buf = bytearray(data)
    sig_off = len(buf) - RSA_SIG_SIZE
    if name == "bl31.bin":
        buf[4:8] = bytes(4)
    buf[sig_off:] = sign_pss(stage2_key, bytes(buf[:sig_off]))
    if name == "bl31.bin":
        buf[4:8] = header_digest(buf)
    return bytes(buf)

if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Sign Exynos9810 images")
    ap.add_argument("input_file", help="Path to the image to sign")
    ap.add_argument("keys_dir",  help="Directory containing the signing keys")
    ap.add_argument("sbl1_json", help="sbl1.json file containing sig info")
    args = ap.parse_args()

    src = Path(args.input_file)
    keys = Path(args.keys_dir)

    st1_privatekey = load_private_key(keys / "st1.pem")
    st2_privatekey = load_private_key(keys / "st2.pem")
    hmac_key = (keys / "hmac.bin").read_bytes()

    data = src.read_bytes()
    if src.name == "fwbl1.bin":
        signed = sign_fwbl1(data, args.sbl1_json, st1_privatekey, pubkey_blob(st2_privatekey.public_key()), hmac_key)
    else:
        signed = sign_compact(src.name, data, st2_privatekey)
    src.write_bytes(signed)
