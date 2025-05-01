from .msg_obj_abc import MsgObject


class EnableRegistration(MsgObject):
    """Represents a message sent by the controller to enable the registration of the drone.

    This message typically carries no payload and is used to signal the drone to start the registration process.
    """    
    @staticmethod
    def deserialize(payload: bytes | None = None, offset: int = 0) -> tuple[int, "EnableRegistration"]:
        """Deserializes the EnableRegistration message from a byte payload.

        Args:
            payload (bytes | None): The byte stream to deserialize (Defaults to None).
            offset (int): Byte offset to begin deserialization (Defaults to 0).
        Returns:
            tuple[int, EnableRegistration]: the new offset and a deserialized EnableRegistration instance.
        """        
        return (offset, EnableRegistration())

    def serialize(self) -> bytes:
        """Serializes the EnableRegistration message into a byte payload.

        Returns:
            bytes: An empty byte string, as this message typically carries no payload.
        """        
        return b""
