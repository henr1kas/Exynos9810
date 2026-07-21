from dataclasses import dataclass

@dataclass(frozen=True)
class Image:
    name: str
    stage: str | None = "st2"
    update_header: bool = False
    ree: bool = False
    avb: str = ""
    size: int = 0
    split: tuple["Image", ...] = ()

@dataclass(frozen=True)
class SoC:
    signing_type: int
    odin: tuple[Image, ...]
