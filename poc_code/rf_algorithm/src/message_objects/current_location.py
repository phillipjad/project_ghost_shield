import struct

class CurrentLocation:
    def __init__(self, x: float, y: float, z: float):
        self.x = x
        self.y = y
        self.z = z

    @staticmethod
    def deserialize(payload: bytes, offset: int = 0) -> tuple[int, "CurrentLocation"]:
        x, y, z = struct.unpack_from('!fff', payload, offset)
        offset += 4
        return CurrentLocation(x, y, z)

    def serialize(self) -> bytes:
        return struct.pack('!fff', self.x, self.y, self.z)