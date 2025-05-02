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
from message_objects.command_ack import CommandAck
from message_objects.confirm_reg import ConfirmRegistration
from message_objects.current_location import CurrentLocation
from message_objects.disable_jammer import DisableJammer
from message_objects.disable_rf_decep import DisableRFDeception
from message_objects.enable_jammer import EnableJammer
from message_objects.enable_reg import EnableRegistration
from message_objects.enable_rf_deception import EnableRFDeception
from message_objects.get_location import GetLocation
from message_objects.move_location import MoveLocation
from message_objects.msg_obj_abc import MsgObject
from message_objects.jammer_disabled import JammerDisabled
from message_objects.jammer_enabled import JammerEnabled

""" The Message class handles creating, signing, verifying, serializing, and deserializing different 
types of secure drone communication messages.    
"""
class Message:
    signing_key_bytes: bytes = load_system_config(SYSTEM_CONFIG_PATH)[4]["private_key"].encode()
    signing_key: SigningKey = SigningKey(signing_key_bytes, encoder=Base64Encoder)

    """ Constructor which initalizes the header and payload. """
    def __init__(self, header: Header, payload: MsgObject | None) -> None:
        self.header = header
        self.payload = payload

    # CRC and signature
    """ Verifies the digital signature and validating the integrity of the message (with CRC).

    Returns:
        bytes: original message data or None if the checksums don't match.
    """
    @staticmethod
    def check_crc_and_signature(msg: SignedMessage) -> bytes | None:
        unsigned_msg = Message.signing_key.verify_key.verify(msg)
        crc = struct.unpack_from("!I", unsigned_msg, 0)[0]
        reconstructed_crc = crc32c.crc32c(unsigned_msg[4:])
        if crc == reconstructed_crc:
            return unsigned_msg[4:]

        return None

    """ Prepares the message for sending by signing and adding a CRC

    Returns:
        SignedMessage: CRC & message as the payload and digital signature.
    """
    @staticmethod
    def sign_and_crc(msg: bytes) -> SignedMessage:
        crc = crc32c.crc32c(msg)
        msg = struct.pack(f"!I{len(msg)}s", crc, msg)
        return Message.signing_key.sign(msg)

    # Message helper functions
    """ Extracts the message type from the message header.

    Returns:
        int: Represents the message type that was passed in.
    """
    @staticmethod
    def get_msg_type(msg: SignedMessage) -> int:
        # Offset=72 to skip the signature, crc, and source id bytes.
        return struct.unpack_from("!B", msg, offset=72)[0]

    """ Extracts the source ID from the SignedMessage object.

    Returns:
        str: 4-character string that represents the source device ID.
    """
    @staticmethod
    def get_source_id(msg: SignedMessage) -> str:
        return struct.unpack_from("!4s", msg, offset=68)[0].decode("utf-8")

    # Serializing methods
    """ Creates digital signature for the message type "Current Location".

    Returns:
        SignedMessage: Digitally signed header, payload, and message for current location.
    """
    @staticmethod
    def get_curr_loc_msg(d_id: str, x: float, y: float, z: float) -> SignedMessage:
        msg_type = MSG_STR_INT_MAP.get(MSG_STR_E.CURRENT_LOCATION)

        payload: bytes = struct.pack("!fff", x, y, z)
        header: bytes = Header(d_id, msg_type, len(payload)).to_bytes()
        msg = struct.pack(f"!{len(header)}s{len(payload)}s", header, payload)
        return Message.sign_and_crc(msg)

    """ Creates digital signature for the message type "Move Location".

    Returns:
        SignedMessage: Digitally signed header, payload, and message for move location.
    """
    @staticmethod
    def get_move_location(d_id: str, x: float, y: float, z: float) -> SignedMessage:
        msg_type = MSG_STR_INT_MAP.get(MSG_STR_E.MOVE_LOCATION)

        payload: bytes = struct.pack("!fff", x, y, z)
        header: bytes = Header(d_id, msg_type, len(payload)).to_bytes()
        msg = struct.pack(f"!{len(header)}s{len(payload)}s", header, payload)
        return Message.sign_and_crc(msg)

    """ Creates digital signature for the message type "Enable Jammer".

    Returns:
        SignedMessage: Digitally signed header, payload, and message for enable jammer.
    """
    @staticmethod
    def get_enable_jammer(d_id: str, duration: float) -> SignedMessage:
        msg_type = MSG_STR_INT_MAP.get(MSG_STR_E.ENABLE_JAMMER)

        payload: bytes = struct.pack("!f", duration)
        header: bytes = Header(d_id, msg_type, len(payload)).to_bytes()
        msg = struct.pack(f"!{len(header)}s{len(payload)}s", header, payload)
        return Message.sign_and_crc(msg)

    """ Creates digital signature for the message type "Disable Jammer".

    Returns:
        SignedMessage: Digitally signed header, payload, and message for disable jammer.
    """
    @staticmethod
    def get_disable_jammer(d_id: str, disable_delay: float) -> SignedMessage:
        msg_type = MSG_STR_INT_MAP.get(MSG_STR_E.DISABLE_JAMMER)

        payload: bytes = struct.pack("!f", disable_delay)
        header: bytes = Header(d_id, msg_type, len(payload)).to_bytes()
        msg = struct.pack(f"!{len(header)}s{len(payload)}s", header, payload)
        return Message.sign_and_crc(msg)

    """ Creates digital signature for the message type "Enable Registration".

    Returns:
        SignedMessage: Digitally signed header and message for enable registration.
    """
    @staticmethod
    def get_enable_registration(d_id: str) -> SignedMessage:
        msg_type = MSG_STR_INT_MAP.get(MSG_STR_E.ENABLE_REGISTRATION)

        header: bytes = Header(d_id, msg_type, 0).to_bytes()
        msg = struct.pack(f"!{len(header)}s", header)
        return Message.sign_and_crc(msg)

    """ Creates digital signature for the message type "Confirm Registration".

    Returns:
        SignedMessage: Digitally signed header, payload, and message for confirm registration.
    """
    @staticmethod
    def get_confirm_registration(d_id: str) -> SignedMessage:
        msg_type = MSG_STR_INT_MAP.get(MSG_STR_E.CONFIRM_REGISTRATION)

        payload: bytes = struct.pack("!4s", d_id.encode())
        header: bytes = Header(d_id, msg_type, len(d_id.encode())).to_bytes()
        msg = struct.pack(f"!{len(header)}s{len(payload)}s", header, payload)
        return Message.sign_and_crc(msg)

    """ Creates digital signature for the message type "Enable RF Deception".

    Returns:
        SignedMessage: Digitally signed header, payload, and message for enable rf deception.
    """
    @staticmethod
    def get_enable_rf_deception(d_id: str, duration: float) -> SignedMessage:
        msg_type = MSG_STR_INT_MAP.get(MSG_STR_E.ENABLE_RF_DECEPTION)

        payload: bytes = struct.pack("!f", duration)
        header: bytes = Header(d_id, msg_type, len(payload)).to_bytes()
        msg = struct.pack(f"!{len(header)}s{len(payload)}s", header, payload)
        return Message.sign_and_crc(msg)

    """ Creates digital signature for the message type "Disable RF Deception".

    Returns:
        SignedMessage: Digitally signed header, payload, and message for disable rf deception.
    """
    @staticmethod
    def get_disable_rf_deception(d_id: str, delay: float) -> SignedMessage:
        msg_type = MSG_STR_INT_MAP.get(MSG_STR_E.DISABLE_RF_DECEPTION)

        payload: bytes = struct.pack("!f", delay)
        header: bytes = Header(d_id, msg_type, len(payload)).to_bytes()
        msg = struct.pack(f"!{len(header)}s{len(payload)}s", header, payload)
        return Message.sign_and_crc(msg)

    """ Creates digital signature for the message type "Get Location".

    Returns:
        SignedMessage: Digitally signed header and message for get location.
    """
    @staticmethod
    def get_location(d_id: str) -> SignedMessage:
        msg_type = MSG_STR_INT_MAP.get(MSG_STR_E.GET_LOCATION)

        header: bytes = Header(d_id, msg_type, 0).to_bytes()
        msg = struct.pack(f"!{len(header)}s", header)
        return Message.sign_and_crc(msg)

    """ Creates digital signature for the message type "Command Ack".

    Returns:
        SignedMessage: Digitally signed header and message for command.
    """
    @staticmethod
    def get_command_ack(d_id: str) -> SignedMessage:
        msg_type = MSG_STR_INT_MAP.get(MSG_STR_E.COMMAND_ACK)

        header: bytes = Header(d_id, msg_type, 0).to_bytes()
        msg = struct.pack(f"!{len(header)}s", header)
        return Message.sign_and_crc(msg)
    
    """ Creates digital signature for the message type "Jammer Enabled".

    Returns:
        SignedMessage: Digitally signed header and message jammer enabled.
    """
    @staticmethod
    def get_jammer_enabled(d_id: str) -> SignedMessage:
        msg_type = MSG_STR_INT_MAP.get(MSG_STR_E.JAMMER_ENABLED)

        header: bytes = Header(d_id, msg_type, 0).to_bytes()
        msg = struct.pack(f"!{len(header)}s", header)
        return Message.sign_and_crc(msg)


    """ Creates digital signature for the message type "Jammer Disabled".

    Returns:
        SignedMessage: Digitally signed header and message for jammer disabled.
    """    
    @staticmethod
    def get_jammer_disabled(d_id: str) -> SignedMessage:
        msg_type = MSG_STR_INT_MAP.get(MSG_STR_E.JAMMER_DISABLED)

        header: bytes = Header(d_id, msg_type, 0).to_bytes()
        msg = struct.pack(f"!{len(header)}s", header)
        return Message.sign_and_crc(msg)

    # Deserializing methods
    """ Deserializes a digitally signed "Current Location" message into a usable Message object.

    Returns:
        Message: Extracted header and payload.
    """
    @staticmethod
    def curr_loc(msg: SignedMessage) -> "Message":
        msg: bytes = Message.check_crc_and_signature(msg)
        header: Header = Header.from_bytes(msg[0:HEADER_SIZE_BYTES])
        payload: CurrentLocation = CurrentLocation.deserialize(msg[HEADER_SIZE_BYTES:])[1]
        return Message(header, payload)

    """ Deserializes a digitally signed "Move Location" message into a usable Message object.

    Returns:
        Message: Extracted header and payload.
    """
    @staticmethod
    def move_loc(msg: SignedMessage) -> "Message":
        msg = Message.check_crc_and_signature(msg)
        header = Header.from_bytes(msg[0:HEADER_SIZE_BYTES])
        payload: MoveLocation = MoveLocation.deserialize(msg[HEADER_SIZE_BYTES:])[1]
        return Message(header, payload)

    """ Deserializes a digitally signed "Enable Jammer" message into a usable Message object.

    Returns:
        Message: Extracted header and payload.
    """
    @staticmethod
    def enable_jammer(msg: SignedMessage) -> "Message":
        msg = Message.check_crc_and_signature(msg)
        header = Header.from_bytes(msg[0:HEADER_SIZE_BYTES])
        payload: EnableJammer = EnableJammer.deserialize(msg[HEADER_SIZE_BYTES:])[1]
        return Message(header, payload)

    """ Deserializes a digitally signed "Disable Jammer" message into a usable Message object.

    Returns:
        Message: Extracted header and payload.
    """
    @staticmethod
    def disable_jammer(msg: SignedMessage) -> "Message":
        msg = Message.check_crc_and_signature(msg)
        header = Header.from_bytes(msg[0:HEADER_SIZE_BYTES])
        payload: DisableJammer = DisableJammer.deserialize(msg[HEADER_SIZE_BYTES:])[1]
        return Message(header, payload)

    """ Deserializes a digitally signed "Enable Registration" message into a usable Message object.

    Returns:
        Message: Extracted header and payload.
    """
    @staticmethod
    def enable_registration(msg: SignedMessage) -> "Message":
        msg = Message.check_crc_and_signature(msg)
        header = Header.from_bytes(msg[0:HEADER_SIZE_BYTES])
        payload = EnableRegistration.deserialize(msg[HEADER_SIZE_BYTES:])[1]
        return Message(header, payload)

    """ Deserializes a digitally signed "Confirm Registration" message into a usable Message object.

    Returns:
        Message: Extracted header and payload.
    """
    @staticmethod
    def confirm_registration(msg: SignedMessage) -> "Message":
        msg = Message.check_crc_and_signature(msg)
        header = Header.from_bytes(msg[0:HEADER_SIZE_BYTES])
        payload = ConfirmRegistration.deserialize(msg[HEADER_SIZE_BYTES:])[1]
        return Message(header, payload)

    """ Deserializes a digitally signed "Enable RF Deception" message into a usable Message object.

    Returns:
        Message: Extracted header and payload.
    """
    @staticmethod
    def enable_rf_deception(msg: SignedMessage) -> "Message":
        msg = Message.check_crc_and_signature(msg)
        header = Header.from_bytes(msg[0:HEADER_SIZE_BYTES])
        payload = EnableRFDeception.deserialize(msg[HEADER_SIZE_BYTES:])[1]
        return Message(header, payload)

    """ Deserializes a digitally signed "Disable RF Deception" message into a usable Message object.

    Returns:
        Message: Extracted header and payload.
    """
    @staticmethod
    def disable_rf_deception(msg: SignedMessage) -> "Message":
        msg = Message.check_crc_and_signature(msg)
        header = Header.from_bytes(msg[0:HEADER_SIZE_BYTES])
        payload = DisableRFDeception.deserialize(msg[HEADER_SIZE_BYTES:])[1]
        return Message(header, payload)

    """ Deserializes a digitally signed "Get Location" message into a usable Message object.

    Returns:
        Message: Extracted header and payload.
    """
    @staticmethod
    def location(msg: SignedMessage) -> "Message":
        msg = Message.check_crc_and_signature(msg)
        header = Header.from_bytes(msg[0:HEADER_SIZE_BYTES])
        payload = GetLocation.deserialize(msg[HEADER_SIZE_BYTES:])[1]
        return Message(header, payload)

    """ Deserializes a digitally signed "Command Ack" message into a usable Message object.

    Returns:
        Message: Extracted header and payload.
    """
    @staticmethod
    def command_ack(msg: SignedMessage) -> "Message":
        msg = Message.check_crc_and_signature(msg)
        header = Header.from_bytes(msg[0:HEADER_SIZE_BYTES])
        payload = CommandAck.deserialize(msg[HEADER_SIZE_BYTES:])[1]
        return Message(header, payload)
    
    """ Deserializes a digitally signed "Jammer Enabled" message into a usable Message object.

    Returns:
        Message: Extracted header and payload.
    """
    @staticmethod
    def jammer_enabled(msg: SignedMessage) -> "Message":
        msg = Message.check_crc_and_signature(msg)
        header = Header.from_bytes(msg[0:HEADER_SIZE_BYTES])
        payload = JammerEnabled.deserialize(msg[HEADER_SIZE_BYTES:])[1]
        return Message(header, payload)


    """ Deserializes a digitally signed "Jammer Disabled" message into a usable Message object.

    Returns:
        Message: Extracted header and payload.
    """
    @staticmethod
    def jammer_disabled(msg: SignedMessage) -> "Message":
        msg = Message.check_crc_and_signature(msg)
        header = Header.from_bytes(msg[0:HEADER_SIZE_BYTES])
        payload = JammerDisabled.deserialize(msg[HEADER_SIZE_BYTES:])[1]
        return Message(header, payload)

    """ Detects the type of a signed message and deserializes it into a Message object using the correct handler function.

    Returns:
        Message or None: Optional message object. None if the message type is invalid.
    """
    @staticmethod
    def deserialize_msg(msg: SignedMessage) -> Optional["Message"]:
        deserialize_function_map: dict[int, callable] = {
            MSG_STR_INT_MAP[MSG_STR_E.CURRENT_LOCATION]: Message.curr_loc,
            MSG_STR_INT_MAP[MSG_STR_E.MOVE_LOCATION]: Message.move_loc,
            MSG_STR_INT_MAP[MSG_STR_E.ENABLE_JAMMER]: Message.enable_jammer,
            MSG_STR_INT_MAP[MSG_STR_E.DISABLE_JAMMER]: Message.disable_jammer,
            MSG_STR_INT_MAP[MSG_STR_E.ENABLE_RF_DECEPTION]: Message.enable_rf_deception,
            MSG_STR_INT_MAP[MSG_STR_E.DISABLE_RF_DECEPTION]: Message.disable_rf_deception,
            MSG_STR_INT_MAP[MSG_STR_E.ENABLE_REGISTRATION]: Message.enable_registration,
            MSG_STR_INT_MAP[MSG_STR_E.CONFIRM_REGISTRATION]: Message.confirm_registration,
            MSG_STR_INT_MAP[MSG_STR_E.GET_LOCATION]: Message.location,
            MSG_STR_INT_MAP[MSG_STR_E.COMMAND_ACK]: Message.command_ack,
            MSG_STR_INT_MAP[MSG_STR_E.JAMMER_ENABLED]: Message.jammer_enabled,
            MSG_STR_INT_MAP[MSG_STR_E.JAMMER_DISABLED]: Message.jammer_disabled,
        }

        try:
            msg_type = Message.get_msg_type(msg)
            return deserialize_function_map[msg_type](msg)
        except AttributeError:
            return None

    """ Serializes a digitally signed message of the requested type with the provided arguments.

    Returns:
        Message or None: Optional SignedMessage object which contains digital signature and CRC.
    """
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
            MSG_STR_INT_MAP.get(MSG_STR_E.GET_LOCATION): Message.get_location,
            MSG_STR_INT_MAP.get(MSG_STR_E.COMMAND_ACK): Message.get_command_ack,
            MSG_STR_INT_MAP.get(MSG_STR_E.JAMMER_ENABLED): Message.get_jammer_enabled,
            MSG_STR_INT_MAP.get(MSG_STR_E.JAMMER_DISABLED): Message.get_jammer_disabled,
        }

        try:
            return serialize_function_map[msg_type](*msg_type_args)
        except AttributeError:
            return None
