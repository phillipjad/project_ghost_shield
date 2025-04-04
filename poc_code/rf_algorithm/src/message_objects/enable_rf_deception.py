import struct

class EnableRFDeception:
    """
    Enable RF Deception
    """
    def __init__(self, duration:float):
        self.float = float

    @staticmethod
    def deserialize(payload: bytes, offset: int = 0) -> tuple[int, "EnableRFDeception"]:
        duration = struct.unpack_from('!f', payload, offset)
        offset += 4
        return EnableRFDeception(duration)

    def serialize(self) -> bytes:
        return struct.pack('!f', self.duration)