from dataclasses import dataclass

@dataclass(frozen=True)
class Image:
    name: str
    size: int | None = None
    stage: str | None = "st2"
    update_header: bool = False

@dataclass(frozen=True)
class SoC:
    sboot: tuple[Image, ...]
    bl: tuple[Image, ...]
