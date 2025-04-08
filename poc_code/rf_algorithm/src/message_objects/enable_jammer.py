import struct

from msg_obj_abc import MsgObject

class EnableJammer(MsgObject):
    def __init__(self, duration: float):
        self.duration = duration

    @staticmethod
    def deserialize(payload: bytes, offset: int = 0) -> tuple[int, "EnableJammer"]:
        duration = struct.unpack_from('!f', payload, offset)
        offset += 4
        return (offset, EnableJammer(duration))

    def serialize(self) -> bytes:
        return struct.pack('!f', self.duration)