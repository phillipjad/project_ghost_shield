import struct

from .msg_obj_abc import MsgObject


class CurrentLocation(MsgObject):
    """Represents a message sent by the drone containing its current location

    This message contains the drone's current coordinates in 3D space (x, y, z).
    """    
    def __init__(self, x: float, y: float, z: float) -> None:
        """Initializes the CurrentLocation message with the drone's coordinates.

        Args:
            x (float): the x-coordinate of the drone.
            y (float): the y-coordinate of the drone.
            z (float): the z-coordinate of the drone.
        """        
        self.x = x
        self.y = y
        self.z = z

    @staticmethod
    def deserialize(payload: bytes, offset: int = 0) -> tuple[int, "CurrentLocation"]:
        x, y, z = struct.unpack_from("!ddd", payload, offset)
        offset += 24
        return (offset, CurrentLocation(x, y, z))

    def serialize(self) -> bytes:
        """Serializes the CurrentLocation message into a byte payload.

        Returns:
            bytes: A byte string representing the x, y, and z coordinates of the drone.
        """        
        return struct.pack("!fff", self.x, self.y, self.z)
