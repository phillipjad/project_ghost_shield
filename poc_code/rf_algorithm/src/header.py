import struct

""" The Header class serialize and deserialize message headers containing device ID, message type, and payload length.
"""
class Header:
    """ Constructor that initalizes the drone id, message type, and payload length. """
    def __init__(self, d_id: str, msg_type: int, payload_length: int) -> None:
        self.d_id = d_id
        self.msg_type = msg_type
        self.payload_length = payload_length

    """ Converts Header's object fields into a packed bytes for manipulation.
    Return:
        bytes: Encoded the drone id, message, and payload of the Header object.
    """
    def to_bytes(self) -> bytes:
        d_id_bytes = self.d_id.encode()
        return struct.pack("!4sBB", d_id_bytes, self.msg_type, self.payload_length)

    """ Unpacks bytes that contain the header object fields. 

    Returns:
        Header: The header object fields that are being decoded.
    """
    @staticmethod
    def from_bytes(header_bytes: bytes) -> "Header":
        d_id, msg_type, payload_length = struct.unpack("!4sBB", header_bytes)
        return Header(d_id, msg_type, payload_length)
