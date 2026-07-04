#!/usr/bin/env python3

import argparse
import hashlib
import hmac
import struct
import time
from pathlib import Path

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa

RSA_SIG_SIZE    = 0x100
RSA_MOD_SIZE    = 0x100
RSA_EXP_SIZE    = 0x4
RSA_PUBKEY_SIZE = 4 + RSA_MOD_SIZE + 4 + RSA_EXP_SIZE
PSS_SALT_SIZE   = 0x20

FWBL1_SIZE          = 0x2000
FWBL1_FOOTER_SIZE   = 0x400
FWBL1_SIGNED_PREFIX = 0x1D0
FWBL1_STAGE2_KEY_OFF = 0x38
FWBL1_BL1_KEY_OFF    = 0x1D0
FWBL1_AUTH_HASH_OFF  = 0x2DC
FWBL1_SIG_SIZE_OFF   = 0x2FC
FWBL1_SIG_OFF        = 0x300

COMPACT_FOOTER_SIZE = 0x110

def u32(v): return struct.pack("<I", v)

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
    return key.sign(data, padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=PSS_SALT_SIZE), hashes.SHA256())[::-1]

def header_digest(data):
    return hashlib.sha256(data[0x10:]).digest()

def sign_fwbl1(data, bl1_key, stage2_pub_blob, hmac_key):
    if len(data) != FWBL1_SIZE:
        raise ValueError(f"fwbl1.bin must be 0x{FWBL1_SIZE:X} bytes")

    buf = bytearray(data)
    fo = len(buf) - FWBL1_FOOTER_SIZE
    bl1_pub = pubkey_blob(bl1_key.public_key())
    auth_hash = hmac.digest(hmac_key, bl1_pub, "sha256")

    buf[0:4] = u32(len(buf) // 512)
    buf[4:8] = bytes(4)
    buf[fo:fo+4]   = u32(4)
    buf[fo+4:fo+8] = b"SLSI"
    buf[fo+8:fo+16] = int(time.time()).to_bytes(8, "little")
    buf[fo+0x14:fo+0x18] = u32(0)
    buf[fo+0x34:fo+0x38] = u32(1)
    buf[fo+FWBL1_STAGE2_KEY_OFF : fo+FWBL1_STAGE2_KEY_OFF+RSA_PUBKEY_SIZE] = stage2_pub_blob
    buf[fo+FWBL1_BL1_KEY_OFF    : fo+FWBL1_BL1_KEY_OFF+RSA_PUBKEY_SIZE]    = bl1_pub
    buf[fo+FWBL1_AUTH_HASH_OFF  : fo+FWBL1_AUTH_HASH_OFF+0x20]             = auth_hash
    buf[fo+FWBL1_SIG_SIZE_OFF   : fo+FWBL1_SIG_SIZE_OFF+4]                 = u32(RSA_SIG_SIZE)

    sig = sign_pss(bl1_key, bytes(buf[:fo + FWBL1_SIGNED_PREFIX]))
    buf[fo+FWBL1_SIG_OFF : fo+FWBL1_SIG_OFF+RSA_SIG_SIZE] = sig
    buf[4:8] = header_digest(buf)[:4]
    return bytes(buf)

def sign_compact(name, data, stage2_key):
    if len(data) < COMPACT_FOOTER_SIZE:
        raise ValueError(f"{name} too small for compact footer")
    buf = bytearray(data)
    sig_off = len(buf) - RSA_SIG_SIZE
    if name == "bl31.bin":
        buf[4:8] = bytes(4)
    buf[sig_off:] = sign_pss(stage2_key, bytes(buf[:sig_off]))
    if name == "bl31.bin":
        buf[4:8] = header_digest(buf)[:4]
    return bytes(buf)

if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Sign Exynos9810 images")
    ap.add_argument("input_file", help="Path to the image to sign")
    ap.add_argument("keys_dir",  help="Directory containing the signing keys")
    args = ap.parse_args()

    src = Path(args.input_file)
    keys = Path(args.keys_dir)

    bl1_key = load_private_key(keys / "st1.pem")
    stage2_key = load_private_key(keys / "st2.pem")
    hmac_key = (keys / "hmac.bin").read_bytes()

    data = src.read_bytes()
    if src.name == "fwbl1.bin":
        signed = sign_fwbl1(data, bl1_key, pubkey_blob(stage2_key.public_key()), hmac_key)
    else:
        signed = sign_compact(src.name, data, stage2_key)
    src.write_bytes(signed)
