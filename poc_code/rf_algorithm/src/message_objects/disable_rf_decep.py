import struct

from .msg_obj_abc import MsgObject


class DisableRFDeception(MsgObject):
    def __init__(self, disable_delay: float) -> None:
        self.disable_delay = disable_delay

    @staticmethod
    def deserialize(payload: bytes, offset: int = 0) -> tuple[int, "DisableRFDeception"]:
        disable_delay = struct.unpack_from("!f", payload, offset)[0]
        offset += 4
        return (offset, DisableRFDeception(disable_delay))

    def serialize(self) -> bytes:
        return struct.pack("!f", self.disable_delay)
