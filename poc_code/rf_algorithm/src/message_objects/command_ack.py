from .msg_obj_abc import MsgObject

class CommandAck(MsgObject):
    """Represents an ACK message sent by the drone to the controller.

    This message is sent in response to a command from the controller.
    It typically carries no payload and is used as a simple confirmation.
    """    
    @staticmethod
    def deserialize(payload: bytes | None = None, offset: int = 0) -> tuple[int, "CommandAck"]:
        """Deserializes the CommandAck message from a byte payload.

        Args:
            payload (bytes | None): The byte stream to deserialize (Defaults to None).
            offset (int): Byte offset to begin deserialization (Defaults to 0).
        Returns:
            tuple[int, CommandAck]: the new offset and a deserialized CommandAck instance.
        """        
        return (offset, CommandAck())

    def serialize(self) -> bytes:
        """Serializes the CommandAck message into a byte payload.

        Returns:
            bytes: An empty byte string, as this message typically carries no payload.
        """        
        return b""
