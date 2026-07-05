from soc import SoC, Image

def soc_data(sboot_size):
    variants = {
        0x2BD210: {
            "sp_size": 0x80000,
            "extra_images": (),
        },
        0x400000: {
            "sp_size": 0x100000,
            "extra_images": (Image("avb.bin", 0xC2DF0, stage=None),),
        }
    }
    cfg = variants[sboot_size]
    return SoC(
        sboot=(
            Image("fwbl1.bin", 0x2000, stage="st1"),
            Image("bl31.bin", 0x13000, update_header=True),
            Image("bl2.bin", 0x4F000),
            Image("pad.bin", 0x19000, stage=None),
            Image("u-boot.bin", 0x180000),
            Image("el3_mon.bin", 0x40000),
            Image("secure_payload.bin", cfg["sp_size"]),
            Image("signerv2.bin", 0x210, stage=None),
            *cfg["extra_images"]
        ),
        bl=(
            Image("cm.bin"),
            Image("keystorage.bin"),
            Image("sboot.bin", sboot_size),
        )
    )