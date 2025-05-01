import struct

from .msg_obj_abc import MsgObject


class EnableJammer(MsgObject):
    """Represents a message sent by the controller to enable the jamming signal on the drone.

    This message contains a duration time in seconds for which the jamming signal should be enabled.
    """    
    def __init__(self, duration: float) -> None:
        """Initializes the EnableJammer message with the duration time.

        Args:
            duration (float): The duration time in seconds for which the jamming signal should be enabled.
        """        
        self.duration = duration

    @staticmethod
    def deserialize(payload: bytes, offset: int = 0) -> tuple[int, "EnableJammer"]:
        """Deserializes a byte payload to extract an EnableJammer message.

        Args:
            payload (bytes): The byte stream to deserialize.
            offset (int): Byte offset to begin deserialization (Defaults to 0).

        Returns:
            tuple[int, EnableJammer]: the new offset and a deserialized EnableJammer instance.
        """        
        duration = struct.unpack_from("!f", payload, offset)[0]
        offset += 4
        return (offset, EnableJammer(duration))

    def serialize(self) -> bytes:
        """Serializes the EnableJammer message into a byte payload.

        Returns:
            bytes: A byte string representing the duration time for which the jamming signal should be enabled.
        """        
        return struct.pack("!f", self.duration)
