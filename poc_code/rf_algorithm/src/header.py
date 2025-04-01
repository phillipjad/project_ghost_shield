import struct

class Header:
    def __init__(self, d_id: str, msg_type: str)-> None:
        self.d_id = d_id
        self.msg_type = msg_type

    def to_bytes(self) -> bytes:
        d_id_bytes = self.d_id.encode()
        msg_type_bytes = self.msg_type.encode()
        return struct.pack(f'!H{len(d_id_bytes)}sH{len(msg_type_bytes)}s', len(d_id_bytes), d_id_bytes, len(msg_type_bytes), msg_type_bytes)
