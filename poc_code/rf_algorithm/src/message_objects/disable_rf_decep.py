import struct

from .msg_obj_abc import MsgObject


class DisableRFDeception(MsgObject):
    """Represents a message sent by the controller to disable the RF deception on the drone.

    This message contains a delay time in seconds before the RF deception is disabled.
    """    
    def __init__(self, disable_delay: float) -> None:
        """Initializes the DisableRFDeception message with the delay time.

        Args:
            disable_delay (float): The delay time in seconds before the RF deception is disabled.
        """        
        self.disable_delay = disable_delay

    @staticmethod
    def deserialize(payload: bytes, offset: int = 0) -> tuple[int, "DisableRFDeception"]:
        """Deserializes a byte payload to extract a DisableRFDeception message.

        Args:
            payload (bytes): The byte stream to deserialize.
            offset (int): Byte offset to begin deserialization (Defaults to 0).

        Returns:
            tuple[int, DisableRFDeception]: the new offset and a deserialized DisableRFDeception instance.
        """        
        disable_delay = struct.unpack_from("!f", payload, offset)[0]
        offset += 4
        return (offset, DisableRFDeception(disable_delay))

    def serialize(self) -> bytes:
        """Serializes the DisableRFDeception message into a byte payload.

        Returns:
            bytes: A byte string representing the delay time before the RF deception is disabled.
        """        
        return struct.pack("!f", self.disable_delay)
