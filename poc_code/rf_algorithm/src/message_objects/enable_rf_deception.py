import struct

from .msg_obj_abc import MsgObject


class EnableRFDeception(MsgObject):
    """Represents a message sent by the controller to enable RF deception on the drone.

    This message contains a duration time in seconds for which the RF deception should be enabled.
    """    

    def __init__(self, duration: float) -> None:
        """Initializes the EnableRFDeception message with the duration time.

        Args:
            duration (float): The duration time in seconds for which the RF deception should be enabled.
        """        
        self.float = duration

    @staticmethod
    def deserialize(payload: bytes, offset: int = 0) -> tuple[int, "EnableRFDeception"]:
        """Deserializes a byte payload to extract an EnableRFDeception message.

        Args:
            payload (bytes): The byte stream to deserialize.
            offset (int): Byte offset to begin deserialization (Defaults to 0).
            
        Returns:
            tuple[int, EnableRFDeception]: the new offset and a deserialized EnableRFDeception instance.
        """        
        duration = struct.unpack_from("!f", payload, offset)
        offset += 4
        return EnableRFDeception(duration)

    def serialize(self) -> bytes:
        """Serializes the EnableRFDeception message into a byte payload.

        Returns:
            bytes: A byte string representing the duration time for which the RF deception should be enabled.
        """        
        return struct.pack("!f", self.duration)
