import struct
from header import Header
import crc32c
from nacl.signing import SigningKey, SignedMessage
from nacl.encoding import Base64Encoder
from helpers.io_helpers import load_system_config
from constants.path_constants import SYSTEM_CONFIG_PATH
from constants.messaging_constants import MSG_STR_E, MSG_STR_INT_MAP
from constants.proj_constants import HEADER_SIZE_BYTES
from message_objects.current_location import CurrentLocation
from message_objects.msg_obj_abc import MsgObject
from message_objects.enable_reg import EnableRegistration
from message_objects.confirm_reg import ConfirmRegistration

class Message:
    signing_key_bytes: bytes = load_system_config(SYSTEM_CONFIG_PATH)[4]["private_key"].encode()
    signing_key: SigningKey = SigningKey(signing_key_bytes, encoder=Base64Encoder)

    def __init__(self, header: Header, payload: MsgObject | None):
        self.header = header
        self.payload = payload

    # CRC and signature
    @staticmethod
    def check_crc_and_signature(msg: SignedMessage) -> bytes | None:
        unsigned_msg = Message.signing_key.verify_key.verify(msg, encoder=Base64Encoder)
        crc = struct.unpack_from('I', unsigned_msg, 0)
        reconstructed_crc = crc32c.crc32c(unsigned_msg[4:])
        if crc == reconstructed_crc:
            return unsigned_msg[4:]
        return None

    @staticmethod
    def sign_and_crc(msg: bytes) -> SignedMessage:
        crc = crc32c.crc32c(msg)
        msg = struct.pack(f'!I{len(msg)}s', crc, msg)
        return Message.signing_key.sign(msg, encoder=Base64Encoder)


    # Serializing methods
    @staticmethod
    def get_curr_loc_msg(d_id: str, x: float, y: float, z: float) -> SignedMessage:
        msg_type = MSG_STR_E.CURRENT_LOCATION
        
        payload: bytes = struct.pack('!fff', x, y, z) 
        header: bytes = Header(d_id, msg_type, len(payload)).to_bytes()
        msg = struct.pack(f'!{len(header)}s{len(payload)}s', header, payload)
        return Message.sign_and_crc(msg)

    def get_enable_registration(d_id: str) -> "Message":
        msg_type = MSG_STR_E.CONTROLLER_ENABLE_REGISTRATION

        header: bytes = Header.from_bytes(d_id, msg_type, 0).to_bytes()
        msg = struct.pack(f'!{len(header)}s')
        return Message.sign_and_crc(msg)

    def get_confirm_registration(d_id: str) -> "Message":
        msg_type = MSG_STR_E.DRONE_CONFIRM_REGISTRATION

        header: bytes = Header.from_bytes(d_id, msg_type, 0).to_bytes()
        msg = struct.pack(f'!{len(header)}s')
        return Message.sign_and_crc(msg)
    

    # Deserializing methods
    def curr_loc(msg: SignedMessage) -> "Message":
        msg: bytes = Message.check_crc_and_signature(msg)
        header: Header = Header.from_bytes(msg[0:HEADER_SIZE_BYTES])
        payload: CurrentLocation = CurrentLocation.deserialize(msg[HEADER_SIZE_BYTES:])
        return Message(header, payload)

    def enable_registration(msg: SignedMessage) -> "Message":
        msg = Message.check_crc_and_signature(msg)
        header = Header.from_bytes(msg[0:HEADER_SIZE_BYTES])
        payload = EnableRegistration()
        return Message(header, payload)

    def confirm_registration(msg: SignedMessage) -> "Message":
        msg = Message.check_crc_and_signature(msg)
        header = Header.from_bytes(msg[0:HEADER_SIZE_BYTES])
        payload = ConfirmRegistration.deserialize(msg[HEADER_SIZE_BYTES:])
        return Message(header, payload)
        

    
    
# m = Message.curr_loc("DRN1", MSG_STR_INT_MAP.get(MSG_STR_E.CURRENT_LOCATION), 10.0, 20.0, 30.0)
# print(m)
# offset = 0
# m = Message.signing_key_yeayaeaieubfa.verify_key.verify(m) 
# crc = struct.unpack_from(f'!I', m, offset)[0]
# offset += 4
# d_id = struct.unpack_from(f'!4s', m, offset)[0].decode()
# offset += 4
# msg_type = struct.unpack_from(f'!B', m, offset)[0]
# offset += 1
# payload_length = struct.unpack_from(f'!B', m, offset)[0]
# offset += 1
# x, y, z = struct.unpack_from('!fff', m, offset)
# print(f"Drone ID: {d_id}, Message Type: {msg_type}, Coordinates: ({x}, {y}, {z})")
#     def __str__(self) -> str:
#         return f"""
#             Drone {self.id}
#             X Coordinate: {self.x}
#             Y Coordinate: {self.y}
#             Z Coordinate: {self.z}
#         """
#
