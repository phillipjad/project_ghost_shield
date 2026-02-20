import struct

from .msg_obj_abc import MsgObject


class EnableRFDeception(MsgObject):
    """
    Enable RF Deception
    """

    def __init__(self, duration: float) -> None:
        self.float = duration

    @staticmethod
    def deserialize(payload: bytes, offset: int = 0) -> tuple[int, "EnableRFDeception"]:
        duration = struct.unpack_from("!f", payload, offset)
        offset += 4
        return EnableRFDeception(duration)

    def serialize(self) -> bytes:
        return struct.pack("!f", self.duration)
