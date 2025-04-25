import struct
from typing import Optional

import crc32c
from nacl.encoding import Base64Encoder
from nacl.signing import SignedMessage, SigningKey

from constants.messaging_constants import MSG_STR_E, MSG_STR_INT_MAP
from constants.path_constants import SYSTEM_CONFIG_PATH
from constants.proj_constants import HEADER_SIZE_BYTES
from header import Header
from helpers.io_helpers import load_system_config
from message_objects.confirm_reg import ConfirmRegistration
from message_objects.current_location import CurrentLocation
from message_objects.disable_jammer import DisableJammer
from message_objects.disable_rf_decep import DisableRFDeception
from message_objects.enable_jammer import EnableJammer
from message_objects.enable_reg import EnableRegistration
from message_objects.enable_rf_deception import EnableRFDeception
from message_objects.move_location import MoveLocation
from message_objects.msg_obj_abc import MsgObject


class Message:
    signing_key_bytes: bytes = load_system_config(SYSTEM_CONFIG_PATH)[4][
        "private_key"
    ].encode()
    signing_key: SigningKey = SigningKey(signing_key_bytes, encoder=Base64Encoder)

    def __init__(self, header: Header, payload: MsgObject | None) -> None:
        self.header = header
        self.payload = payload

    # CRC and signature
    @staticmethod
    def check_crc_and_signature(msg: SignedMessage) -> bytes | None:
        unsigned_msg = Message.signing_key.verify_key.verify(msg)
        crc = struct.unpack_from("!I", unsigned_msg, 0)[0]
        reconstructed_crc = crc32c.crc32c(unsigned_msg[4:])
        if crc == reconstructed_crc:
            return unsigned_msg[4:]

        return None

    @staticmethod
    def sign_and_crc(msg: bytes) -> SignedMessage:
        crc = crc32c.crc32c(msg)
        msg = struct.pack(f"!I{len(msg)}s", crc, msg)
        return Message.signing_key.sign(msg)

    # Message helper functions
    @staticmethod
    def get_msg_type(msg: SignedMessage) -> int:
        # Offset=72 to skip the signature, crc, and source id bytes.
        return struct.unpack_from("!B", msg, offset=72)[0]

    def get_source_id(msg: SignedMessage) -> str:
        return struct.unpack_from("!4s", msg, offset=68)[0].decode("utf-8")

    # Serializing methods
    @staticmethod
    def get_curr_loc_msg(d_id: str, x: float, y: float, z: float) -> SignedMessage:
        msg_type = MSG_STR_INT_MAP.get(MSG_STR_E.CURRENT_LOCATION)

        payload: bytes = struct.pack("!fff", x, y, z)
        header: bytes = Header(d_id, msg_type, len(payload)).to_bytes()
        msg = struct.pack(f"!{len(header)}s{len(payload)}s", header, payload)
        return Message.sign_and_crc(msg)

    @staticmethod
    def get_move_location(d_id: str, x: float, y: float, z: float) -> SignedMessage:
        msg_type = MSG_STR_INT_MAP.get(MSG_STR_E.MOVE_LOCATION)

        payload: bytes = struct.pack("!fff", x, y, z)
        header: bytes = Header(d_id, msg_type, len(payload)).to_bytes()
        msg = struct.pack(f"!{len(header)}s{len(payload)}s", header, payload)
        return Message.sign_and_crc(msg)

    @staticmethod
    def get_enable_jammer(d_id: str, duration: float) -> SignedMessage:
        msg_type = MSG_STR_INT_MAP.get(MSG_STR_E.ENABLE_JAMMER)

        payload: bytes = struct.pack("!f", duration)
        header: bytes = Header(d_id, msg_type, len(payload)).to_bytes()
        msg = struct.pack(f"!{len(header)}s{len(payload)}s", header, payload)
        return Message.sign_and_crc(msg)

    @staticmethod
    def get_disable_jammer(d_id: str, disable_delay: float) -> SignedMessage:
        msg_type = MSG_STR_INT_MAP.get(MSG_STR_E.DISABLE_JAMMER)

        payload: bytes = struct.pack("!f", disable_delay)
        header: bytes = Header(d_id, msg_type, len(payload)).to_bytes()
        msg = struct.pack(f"!{len(header)}s{len(payload)}s", header, payload)
        return Message.sign_and_crc(msg)

    @staticmethod
    def get_enable_registration(d_id: str) -> SignedMessage:
        msg_type = MSG_STR_INT_MAP.get(MSG_STR_E.ENABLE_REGISTRATION)

        header: bytes = Header(d_id, msg_type, 0).to_bytes()
        msg = struct.pack(f"!{len(header)}s", header)
        return Message.sign_and_crc(msg)

    @staticmethod
    def get_confirm_registration(d_id: str) -> SignedMessage:
        msg_type = MSG_STR_INT_MAP.get(MSG_STR_E.CONFIRM_REGISTRATION)

        payload: bytes = struct.pack("!4s", d_id.encode())
        header: bytes = Header(d_id, msg_type, len(d_id.encode())).to_bytes()
        msg = struct.pack(f"!{len(header)}s{len(payload)}s", header, payload)
        return Message.sign_and_crc(msg)

    @staticmethod
    def get_enable_rf_deception(d_id: str, duration: float) -> SignedMessage:
        msg_type = MSG_STR_INT_MAP.get(MSG_STR_E.ENABLE_RF_DECEPTION)

        payload: bytes = struct.pack("!f", duration)
        header: bytes = Header(d_id, msg_type, len(payload)).to_bytes()
        msg = struct.pack(f"!{len(header)}s{len(payload)}s", header, payload)
        return Message.sign_and_crc(msg)

    @staticmethod
    def get_disable_rf_deception(d_id: str, delay: float) -> SignedMessage:
        msg_type = MSG_STR_INT_MAP.get(MSG_STR_E.DISABLE_RF_DECEPTION)

        payload: bytes = struct.pack("!f", delay)
        header: bytes = Header(d_id, msg_type, len(payload)).to_bytes()
        msg = struct.pack(f"!{len(header)}s{len(payload)}s", header, payload)
        return Message.sign_and_crc(msg)

    # Deserializing methods
    @staticmethod
    def curr_loc(msg: SignedMessage) -> "Message":
        msg: bytes = Message.check_crc_and_signature(msg)
        header: Header = Header.from_bytes(msg[0:HEADER_SIZE_BYTES])
        payload: CurrentLocation = CurrentLocation.deserialize(msg[HEADER_SIZE_BYTES:])[1]
        return Message(header, payload)

    @staticmethod
    def move_loc(msg: SignedMessage) -> "Message":
        msg = Message.check_crc_and_signature(msg)
        header = Header(msg[0:HEADER_SIZE_BYTES])
        payload: MoveLocation = MoveLocation.deserialize(msg[HEADER_SIZE_BYTES:])[1]
        return Message(header, payload)

    @staticmethod
    def enable_jammer(msg: SignedMessage) -> "Message":
        msg = Message.check_crc_and_signature(msg)
        header = Header.from_bytes(msg[0:HEADER_SIZE_BYTES])
        payload: EnableJammer = EnableJammer.deserialize(msg[HEADER_SIZE_BYTES:])[1]
        return Message(header, payload)

    @staticmethod
    def disable_jammer(msg: SignedMessage) -> "Message":
        msg = Message.check_crc_and_signature(msg)
        header = Header.from_bytes(msg[0:HEADER_SIZE_BYTES])
        payload: DisableJammer = DisableJammer.deserialize(msg[HEADER_SIZE_BYTES:])[1]
        return Message(header, payload)

    @staticmethod
    def enable_registration(msg: SignedMessage) -> "Message":
        msg = Message.check_crc_and_signature(msg)
        header = Header.from_bytes(msg[0:HEADER_SIZE_BYTES])
        payload = EnableRegistration.deserialize(msg[HEADER_SIZE_BYTES:])[1]
        return Message(header, payload)

    @staticmethod
    def confirm_registration(msg: SignedMessage) -> "Message":
        msg = Message.check_crc_and_signature(msg)
        header = Header.from_bytes(msg[0:HEADER_SIZE_BYTES])
        payload = ConfirmRegistration.deserialize(msg[HEADER_SIZE_BYTES:])[1]
        return Message(header, payload)

    @staticmethod
    def enable_rf_deception(msg: SignedMessage) -> "Message":
        msg = Message.check_crc_and_signature(msg)
        header = Header.from_bytes(msg[0:HEADER_SIZE_BYTES])
        payload = EnableRFDeception.deserialize(msg[HEADER_SIZE_BYTES:])[1]
        return Message(header, payload)

    @staticmethod
    def disable_rf_deception(msg: SignedMessage) -> "Message":
        msg = Message.check_crc_and_signature(msg)
        header = Header.from_bytes(msg[0:HEADER_SIZE_BYTES])
        payload = DisableRFDeception.deserialize(msg[HEADER_SIZE_BYTES:])[1]
        return Message(header, payload)

    @staticmethod
    def deserialize_msg(msg: SignedMessage) -> Optional["Message"]:
        deserialize_function_map: dict[int, callable] = {
            MSG_STR_INT_MAP[MSG_STR_E.CURRENT_LOCATION]: Message.curr_loc,
            MSG_STR_INT_MAP[MSG_STR_E.MOVE_LOCATION]: Message.move_loc,
            MSG_STR_INT_MAP[MSG_STR_E.ENABLE_JAMMER]: Message.enable_jammer,
            MSG_STR_INT_MAP[MSG_STR_E.DISABLE_JAMMER]: Message.disable_jammer,
            MSG_STR_INT_MAP[MSG_STR_E.ENABLE_RF_DECEPTION]: Message.enable_rf_deception,
            MSG_STR_INT_MAP[
                MSG_STR_E.DISABLE_RF_DECEPTION
            ]: Message.disable_rf_deception,
            MSG_STR_INT_MAP[MSG_STR_E.ENABLE_REGISTRATION]: Message.enable_registration,
            MSG_STR_INT_MAP[
                MSG_STR_E.CONFIRM_REGISTRATION
            ]: Message.confirm_registration,
        }

        try:
            msg_type = Message.get_msg_type(msg)
            return deserialize_function_map[msg_type](msg)
        except AttributeError:
            return None

    @staticmethod
    def serialize_msg(msg_type: str, msg_type_args: list[any]) -> SignedMessage | None:
        serialize_function_map: dict[str, callable] = {
            MSG_STR_INT_MAP.get(MSG_STR_E.CURRENT_LOCATION): Message.get_curr_loc_msg,
            MSG_STR_INT_MAP.get(MSG_STR_E.MOVE_LOCATION): Message.get_move_location,
            MSG_STR_INT_MAP.get(MSG_STR_E.ENABLE_JAMMER): Message.get_enable_jammer,
            MSG_STR_INT_MAP.get(MSG_STR_E.DISABLE_JAMMER): Message.get_disable_jammer,
            MSG_STR_INT_MAP.get(MSG_STR_E.ENABLE_RF_DECEPTION): Message.get_enable_rf_deception,
            MSG_STR_INT_MAP.get(MSG_STR_E.DISABLE_RF_DECEPTION): Message.get_disable_rf_deception,
            MSG_STR_INT_MAP.get(MSG_STR_E.ENABLE_REGISTRATION): Message.get_enable_registration,
            MSG_STR_INT_MAP.get(MSG_STR_E.CONFIRM_REGISTRATION): Message.get_confirm_registration,
        }

        try:
            return serialize_function_map[msg_type](*msg_type_args)
        except AttributeError:
            return None