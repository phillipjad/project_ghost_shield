from abc import ABC, abstractmethod


class MsgObject(ABC):
    """Abstract base class for message objects.

    This class defines the interface for all message objects used in the system.
    """    
    @staticmethod
    @abstractmethod
    def deserialize(payload: bytes, offset: int = 0) -> tuple[int, "MsgObject"]:
        """Deserializes a message from a byte payload.

        Args:
            payload (bytes): The byte stream to deserialize.
            offset (int): Byte offset to begin deserialization (Defaults to 0).

        Returns:
            tuple[int, MsgObject]: The new offset and the deserialized message object.
        """        
        pass

    @abstractmethod
    def serialize(self) -> bytes:
        """Serializes the message into a byte payload.

        Returns:
            bytes: The serialized byte stream of the message.
        """        
        pass