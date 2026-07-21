from soc import SoC, Image

def soc_data():
    return SoC(
        signing_type=4,
        odin=(
            Image("dpm.img"),
            Image("harx.bin", ree=True, avb="harx", size=3145728, split=(
                Image("harx.bin", ree=True),
                Image("tail.bin", stage=None), # signerv3, avb footer
            )),
            Image("keystorage.bin", ree=True, avb="keystorage", size=524288, split=(
                Image("keystorage.bin"),
                Image("tail.bin", stage=None), # signerv3, avb footer
            )),
            Image("ldfw.img", ree=True, avb="ldfw", size=8388608, split=(
                Image("ldfw.bin"),
                Image("tail.bin", stage=None), # signerv3, avb footer
            )),
            Image("O1S_EUR_OPENX.pit", ree=True), # TODO: device specific (take any .pit?)
            Image("sboot.bin", ree=True, avb="bootloader", size=4194304, split=(
                Image("bl1.bin", stage="st1"),
                Image("epbl.bin", update_header=True),
                Image("bl2.bin", ree=True),
                Image("pad.bin", stage=None),
                Image("dpm.img"),
                Image("bootload.bin", ree=True),
                Image("el3_mon.bin"),
                Image("tail.bin", stage=None),# 32 evt info, signerv3, avb footer
            )),
            Image("ssp.img", stage=None), # not sure :D
            Image("tzar.img", ree=True),
            Image("tzsw.img", ree=True, avb="tzsw", size=1572864, split=(
                Image("tzsw.bin"),
                Image("tail.bin", stage=None), # signerv3, avb footer
            )),
            Image("uh.bin", ree=True),
            Image("up_param.bin", stage=None),
            Image("vbmeta.img", ree=True), # update other resigned files todo
            Image("vddcal_fw.bin", ree=True),
        )
    )