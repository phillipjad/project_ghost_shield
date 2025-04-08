import struct

from .msg_obj_abc import MsgObject


class DisableJammer(MsgObject):
    def __init__(self, disable_delay: float) -> None:
        self.disable_delay = disable_delay

    @staticmethod
    def deserialize(payload: bytes, offset: int = 0) -> tuple[int, "DisableJammer"]:
        disable_delay = struct.unpack_from("!f", payload, offset)[0]
        offset += 4
        return (offset, DisableJammer(disable_delay))

    def serialize(self) -> bytes:
        return struct.pack("!f", self.disable_delay)
