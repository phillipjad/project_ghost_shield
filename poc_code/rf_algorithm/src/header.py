import struct

class Header:
    def __init__(self, d_id: str, msg_type: str, payload_length: int)-> None:
        self.d_id = d_id
        self.msg_type = msg_type
        self.payload_length = payload_length

    def to_bytes(self) -> bytes:
        d_id_bytes = self.d_id.encode()
        return struct.pack(
            f'!{len(d_id_bytes)}sBB',
            d_id_bytes, self.msg_type, self.payload_length
        )
