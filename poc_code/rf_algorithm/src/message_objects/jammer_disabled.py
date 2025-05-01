from .msg_obj_abc import MsgObject


class JammerDisabled(MsgObject):
    """Represents a message sent by the drone to the controller indicating that the jamming signal has been disabled.

    This message typically carries no payload and is used to confirm the successful disabling of the jamming signal.
    """    
    @staticmethod
    def deserialize(payload: bytes | None = None, offset: int = 0) -> tuple[int, "JammerDisabled"]:
        """Deserializes the JammerDisabled message from a byte payload.

        Args:
            payload (bytes | None): The byte stream to deserialize (Defaults to None).
            offset (int): Byte offset to begin deserialization (Defaults to 0).
        Returns:
            tuple[int, JammerDisabled]: the new offset and a deserialized JammerDisabled instance.
        """        
        return (offset, JammerDisabled())

    def serialize(self) -> bytes:
        """Serializes the JammerDisabled message into a byte payload.

        Returns:
            bytes: An empty byte string, as this message typically carries no payload.
        """        
        return b""
