import struct


class Header:
    def __init__(self, d_id: str, msg_type: int, payload_length: int) -> None:
        self.d_id = d_id
        self.msg_type = msg_type
        self.payload_length = payload_length

    def to_bytes(self) -> bytes:
        d_id_bytes = self.d_id.encode()
        return struct.pack("!4sBB", d_id_bytes, self.msg_type, self.payload_length)

    @staticmethod
    def from_bytes(header_bytes: bytes) -> "Header":
        d_id, msg_type, payload_length = struct.unpack("!4sBB", header_bytes)
        return Header(d_id, msg_type, payload_length)
