import struct

from .msg_obj_abc import MsgObject


class MoveLocation(MsgObject):
    """Represents a message sent by the controller to the drone to move to a specific location.

    This message typically carries the x, y, and z coordinates to which the drone should move.
    """    
    def __init__(self, x: float, y: float, z: float) -> None:
        """Initializes the MoveLocation message with the target coordinates.

        Args:
            x (float): x-coordinate of the target location.
            y (float): y-coordinate of the target location.
            z (float): z-coordinate of the target location.
        """        
        self.x = x
        self.y = y
        self.z = z

    @staticmethod
    def deserialize(payload: bytes, offset: int = 0) -> tuple[int, "MoveLocation"]:
        x, y, z = struct.unpack_from("!ddd", payload, offset)
        offset += 24
        return (offset, MoveLocation(x, y, z))

    def serialize(self) -> bytes:
        """Serializes the MoveLocation message into a byte payload.

        Returns:
            bytes: A byte string representing the x, y, and z coordinates of the target location.
        """        
        return struct.pack("!fff", self.x, self.y, self.z)
