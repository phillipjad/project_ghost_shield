from .msg_obj_abc import MsgObject


class GetLocation(MsgObject):
    """Represents a message sent by the controller to request the drone's current location.

    This message typically carries no payload and is used to signal the drone to send its current coordinates.
    """    
    @staticmethod
    def deserialize(payload: bytes | None = None, offset: int = 0) -> tuple[int, "GetLocation"]:
        """Deserializes the GetLocation message from a byte payload.

        Args:
            payload (bytes | None): The byte stream to deserialize (Defaults to None).
            offset (int): Byte offset to begin deserialization (Defaults to 0).

        Returns:
            tuple[int, GetLocation]: the new offset and a deserialized GetLocation instance.
        """        
        return (offset, GetLocation())

    def serialize(self) -> bytes:
        """Serializes the GetLocation message into a byte payload.

        Returns:
            bytes: An empty byte string, as this message typically carries no payload.
        """        
        return b""
