import struct
from header import Header
import crc32c
from nacl.signing import SigningKey, SignedMessage
from nacl.encoding import Base64Encoder
from helpers.io_helpers import load_system_config
from constants.path_constants import SYSTEM_CONFIG_PATH
from constants.messaging_constants import MSG_STR_E, MSG_STR_INT_MAP
# from nacl.signing import VerifyKey

class Message:
    # def __init__(self, d_id: str, msg_type: str, x: str, y : str, z: str, duration: str)-> None:
    #     self.d_id = d_id
    #     self.msg_type = msg_type
    #     self.x = x
    #     self.y = y
    #     self.z = z
    #     self.duration = duration
    signing_key_bytes: bytes = load_system_config(SYSTEM_CONFIG_PATH)[4]["private_key"].encode()
    signing_key_yeayaeaieubfa: SigningKey

    # Serializing methods
    @staticmethod
    def curr_loc(d_id: str, msg_type:str, x: float, y: float, z: float) -> SignedMessage:
        payload: bytes = struct.pack(f'!fff', x, y, z)
        unsigned_nocrc_header: bytes = Header(d_id, msg_type, len(payload)).to_bytes()
        msg = struct.pack(f'!{len(unsigned_nocrc_header)}s{len(payload)}s', unsigned_nocrc_header, payload)
        msg_w_crc = struct.pack(f'!I{len(msg)}s', crc32c.crc32c(msg), msg)

        Message.signing_key_yeayaeaieubfa = signing_key = SigningKey(Message.signing_key_bytes, encoder=Base64Encoder)
        signed: SignedMessage = signing_key.sign(msg_w_crc)
        
        return signed

    # Deserializing methods
    def curr_loc(msg: bytes) -> "CurrentLocation":
        # msg = Message.signing_key_yeayaeaieubfa.verify_key.verify(m) 
        crc = struct.unpack_from(f'!I', msg, offset)[0]
        offset += 4
        d_id = struct.unpack_from(f'!4s', msg, offset)[0].decode()
        offset += 4
        msg_type = struct.unpack_from(f'!B', msg, offset)[0]
        offset += 1
        payload_length = struct.unpack_from(f'!B', msg, offset)[0]
        offset += 1
        x, y, z = struct.unpack_from('!fff', msg, offset)
        return CurrentLocation(x, y, z)
    
    
m = Message.curr_loc("DRN1", MSG_STR_INT_MAP.get(MSG_STR_E.CURRENT_LOCATION), 10.0, 20.0, 30.0)
print(m)
offset = 0
m = Message.signing_key_yeayaeaieubfa.verify_key.verify(m) 
crc = struct.unpack_from(f'!I', m, offset)[0]
offset += 4
d_id = struct.unpack_from(f'!4s', m, offset)[0].decode()
offset += 4
msg_type = struct.unpack_from(f'!B', m, offset)[0]
offset += 1
payload_length = struct.unpack_from(f'!B', m, offset)[0]
offset += 1
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
