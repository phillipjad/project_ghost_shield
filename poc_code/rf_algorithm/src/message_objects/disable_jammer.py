import struct

from .msg_obj_abc import MsgObject


class DisableJammer(MsgObject):
    """Represents a message sent by the controller to disable the jamming signal on the drone.

    This message contains a delay time in seconds before the jamming signal is disabled.
    """    
    def __init__(self, disable_delay: float) -> None:
        """Initializes the DisableJammer message with the delay time.

        Args:
            disable_delay (float): The delay time in seconds before the jamming signal is disabled.
        """        
        self.disable_delay = disable_delay

    @staticmethod
    def deserialize(payload: bytes, offset: int = 0) -> tuple[int, "DisableJammer"]:
        """Deserializes a byte payload to extract a DisableJammer message.

        Args:
            payload (bytes): The byte stream to deserialize.
            offset (int): Byte offset to begin deserialization (Defaults to 0).
        Returns:
            tuple[int, DisableJammer]: the new offset and a deserialized DisableJammer instance.
        """        
        disable_delay = struct.unpack_from("!f", payload, offset)[0]
        offset += 4
        return (offset, DisableJammer(disable_delay))

    def serialize(self) -> bytes:
        """Serializes the DisableJammer message into a byte payload.

        Returns:
            bytes: A byte string representing the delay time before the jamming signal is disabled.
        """        
        return struct.pack("!f", self.disable_delay)
