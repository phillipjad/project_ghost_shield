import struct

class DisableRFDeception:

    def __init__(self, disable_delay: float):
        self.disable_delay = disable_delay

    @staticmethod
    def deserialize(payload: bytes, offset: int = 0) -> tuple[int, "DisableRFDeception"]:
        disable_delay = struct.unpack_from('!f', payload, offset)
        offset += 4
        return DisableRFDeception(disable_delay)

    def serialize(self) -> bytes:
        return struct.pack('!f', self.disable_delay)
    
