import struct

from .msg_obj_abc import MsgObject


class ConfirmRegistration(MsgObject):
    """
    Represents a message sent by a drone to confirm its registration with the controller
    
    This message contains the drone's unique ID as a 4-byte string.
    """   

    def __init__(self, drone_id: str) -> None:
        """Initializes the ConfirmRegistration message with the drone's ID.

        Args:
            drone_id (str): The unique ID of the drone, represented as a 4-byte string.
        """        
        self.drone_id = drone_id

    @staticmethod
    def deserialize(payload: bytes, offset: int = 0) -> tuple[int, "ConfirmRegistration"]:  
        """Deserializes the ConfirmRegistration message from a byte payload.

        Args:
            payload (bytes): The byte stream to deserialize.
            offset (int): Byte offset to begin deserialization (Defaults to 0).

        Returns:
            tuple[int, ConfirmRegistration]: the new offset and a deserialized ConfirmRegistration instance.
        """            
        drone_id = struct.unpack_from("!4s", payload)[0].decode("utf-8")
        offset += 4
        return (offset, ConfirmRegistration(drone_id))

    def serialize(self) -> bytes:
        """Serializes the ConfirmRegistration message into a byte payload.

        Returns:
            bytes: A 4-byte encoded string representing the drone ID.
        """        
        return struct.pack("!4s", self.drone_id)
    