#!/usr/bin/env python3

import sys
import hashlib
import os
from struct import unpack
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import hashes, serialization

def sign(msg, priv_key):
    return priv_key.sign(
        msg,
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=32,
        ),
        hashes.SHA256(),
    )

def get_signer_info_if_missing(data, filename):
    signerver0 = bytes.fromhex("53 69 67 6E 65 72 56 65 72 30")
    if data == signerver0:
        return None
    print("currently no signerver info, will take from sboot.bin")
    if not os.path.exists("sboot.bin"):
        print("place your device's sboot.bin in current dir and re-run script")
        return
    # sign type v5 todo
    with open("sboot.bin", "rb") as f:
        offset = -(0x210)
        f.seek(offset, os.SEEK_END)
        signer_info = bytearray(f.read(0x210))
    signer_info[0x8C:0x8C+0x64] = filename.encode().ljust(0x64, b"\x00")
    return signer_info

# for bootimg
def get_number_of_pages(size, page_size):
    return (size + page_size - 1) // page_size

def compute_min_size(data):
    (kernel_size, kernel_addr, ramdisk_size, ramdisk_addr,
    second_size, second_addr, tags_addr, page_size,
    dtb_size) = unpack('9I', data[8:44])
    num_header_pages = 1
    num_kernel_pages = get_number_of_pages(kernel_size, page_size)
    num_ramdisk_pages = get_number_of_pages(ramdisk_size, page_size)
    num_second_pages = get_number_of_pages(second_size, page_size)
    num_dtb_pages = get_number_of_pages(dtb_size, page_size)
    return (num_header_pages + num_kernel_pages + num_ramdisk_pages + num_second_pages + num_dtb_pages)*page_size

def main():
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <file> <private_key.pem>")
        sys.exit(1)

    filename = sys.argv[1]
    keyfile = sys.argv[2]
    if not os.path.exists(filename):
        print("file not found!")
        return
    if not os.path.exists(keyfile):
        print("key not found!")
        return
    with open(keyfile, "rb") as f:
        priv_key = serialization.load_pem_private_key(
            f.read(),
            password=None,
        )

    with open(filename, "rb") as f:
        data = bytearray(os.fstat(f.fileno()).st_size)
        f.readinto(data)

    is_sparse = data[:4] == b'\x3a\xff\x26\xed'
    is_bootimg = data[:8] == b'ANDROID!'
    did_expand = False
    signer_info_added = False

    if is_sparse:
        print("sparse detected!")
        signer_info_if_null = get_signer_info_if_missing(data[0x328:0x332], filename)
        if signer_info_if_null is not None:
            signer_info_added = True
            data[0x328:0x428] = signer_info_if_null[:0x100]
        msg = hashlib.sha256(data[0x328:]).digest()
        sig = sign(msg, priv_key)
    else:
        signer_info_if_null = get_signer_info_if_missing(data[-0x210:-0x206], filename)
        if signer_info_if_null is not None:
            did_expand = True
            if is_bootimg:
                print("bootimg detected!")
                sz = compute_min_size(data)
                data = data[:sz]
                seandroidenforce = bytes.fromhex("53 45 41 4E 44 52 4F 49 44 45 4E 46 4F 52 43 45")
                data += seandroidenforce
            data += signer_info_if_null
        else:
            msg = bytes(data[:-0x100])
            sig = sign(msg, priv_key)
    if not did_expand:
        with open(filename, "r+b") as f:
            if is_sparse:
                if signer_info_added:
                    f.seek(0x328)
                    f.write(data[0x328:0x428])
                f.seek(0x28)
            else:
                f.seek(-0x100, 2)
            f.write(sig[::-1])
    else:
        with open(filename, "wb") as f:
            f.write(data)

if __name__ == "__main__":
    main()
