# Custom Key Boot & Fusing Guide

This guide walks through building a custom-signed bootloader, fusing a custom `SEC_BOOT_KEY` on Exynos9810.

## Prerequisites

- `cm.bin`, `keystorage.bin`, `sboot.bin` extracted from stock `BL.tar`
- Python3
- [houston-pub](https://github.com/halal-beef/houston-pub)
- ODIN (for flashing)

## 1. Prepare Files

Copy the following files from `BL.tar` into the `bl/` directory:

```
bl/cm.bin
bl/keystorage.bin
bl/sboot.bin
```

## 2. Split `sboot.bin`

```bash
python split.py bl/sboot.bin
```

This extracts the individual components of `sboot.bin` into a working `sboot/` directory.

## 3. Patch `u-boot.bin`

Run the patch script from inside the `sboot/` directory:

```bash
python patch.py
```

This produces a patched `u-boot.bin`.

**Optional — enable key fusing:**
If you want the patched `sboot.bin` to fuse a custom `SEC_BOOT_KEY` when it later boots from UFS and enters download mode, open `patch.py` *before* running it and set:

```python
should_fuse_key = True
```

If you don't want fusing to happen, leave this flag untouched (default) and simply run `patch.py` as-is.

> ⚠️ **Warning:** Fusing `SEC_BOOT_KEY` is a **one-way, irreversible operation**. Once fused, the device will permanently require boot images signed with your custom key, and this cannot be undone. Only set `should_fuse_key = True` if you fully understand the implications and have verified your setup on a device you are prepared to lose if something goes wrong.

Once `patch.py` has been run (with or without the flag), rename the output to `u-boot.bin`.

## 4. Build the Signed `sboot.bin`

```bash
python build.py
```

This re-signs the files in `bl/` and the `sboot/` components, and produces a new, properly signed `sboot.bin`.

## 5. Boot with the Custom Key

Use `houston.py` to boot the payload with the custom-key boot binary:

```bash
python houston-pub/houston.py -e -p boot_custom_key.bin \
  sboot/fwbl1.bin \
  sboot/bl31.bin \
  sboot/bl2.bin \
  sboot/fwbl1.bin \
  sboot/u-boot.bin \
  sboot/el3_mon.bin
```

## 6. Flash via ODIN

Pack the updated contents of `bl/` into a `.tar` archive and flash it using ODIN.

## 7. Boot from UFS

After flashing, the same payload will attempt to boot from UFS.

> **Note:** This step is not 100% reliable and currently only works on Linux.

Repeat the boot command:

```bash
python houston-pub/houston.py -e -p boot_custom_key.bin \
  sboot/fwbl1.bin \
  sboot/bl31.bin \
  sboot/bl2.bin \
  sboot/fwbl1.bin \
  sboot/u-boot.bin \
  sboot/el3_mon.bin
```

Then try to enter download mode/hold power for boot. If `should_fuse_key` was set in step 3, `SEC_BOOT_KEY` will be fused at this point.

---

## Resources

- [houston-pub](https://github.com/halal-beef/houston-pub) — CVE-2024-56426 implementation
- [CVE-2024-56426 payload reference (SM-G960F)](https://github.com/Creeeeger/CVE-2024-56426/blob/SM-G960F/external/payloads/exynos9820_boot_custom_key/Exynos9820_boot_custom_key.S) — Exynos9810 boot custom key payload
