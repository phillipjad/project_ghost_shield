import struct
import header as header
import crc32c
from nacl.signing import SigningKey
from helpers.io_helpers import load_system_config
# from nacl.signing import VerifyKey

class Message:
    # def __init__(self, d_id: str, msg_type: str, x: str, y : str, z: str, duration: str)-> None:
    #     self.d_id = d_id
    #     self.msg_type = msg_type
    #     self.x = x
    #     self.y = y
    #     self.z = z
    #     self.duration = duration
    signing_key_bytes: bytes = load_system_config()[4]["signing_key"].encode()

    
    @staticmethod
    def curr_loc(d_id: str, msg_type:str, x: float, y: float, z: float) -> "Message":
        fmt = f'!H{len(d_id.encode())}sH{len(msg_type.encode())}sfff'
        payload = struct.pack(fmt, len(d_id.encode()), d_id.encode(), len(msg_type.encode()), msg_type.encode(), x, y, z)
        hdr = header(d_id, msg_type)
        msg = struct.pack('!H', len(hdr.d_id.encode())) + hdr.d_id.encode() + struct.pack('!H', len(hdr.msg_type.encode())) + hdr.msg_type.encode() + msg
        crc = crc32c.cr32c(msg)

        signing_key = SigningKey(Message.signing_key_bytes)
        signed = signing_key.sign(msg)
        
        return msg 
    
    
print(SigningKey(Message.signing_key_bytes).verify_key)
m = Message.curr_loc("drone1", "location", 10.0, 20.0, 30.0)
print(m)
offset = 0
d_len = struct.unpack_from('!H', m, offset)[0]
offset += 2
d_id = struct.unpack_from(f'!{d_len}s', m, offset)[0].decode()
offset += d_len
msg_len = struct.unpack_from('!H', m, offset)[0]
offset += 2
msg_type = struct.unpack_from(f'!{msg_len}s', m, offset)[0].decode()
offset += msg_len
x, y, z = struct.unpack_from('!fff', m, offset)
print(f"Drone ID: {d_id}, Message Type: {msg_type}, Coordinates: ({x}, {y}, {z})")
#     def __str__(self) -> str:
#         return f"""
#             Drone {self.id}
#             X Coordinate: {self.x}
#             Y Coordinate: {self.y}
#             Z Coordinate: {self.z}
#         """
#
