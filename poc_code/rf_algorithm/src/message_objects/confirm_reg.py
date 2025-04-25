import struct

from .msg_obj_abc import MsgObject


class ConfirmRegistration(MsgObject):
    def __init__(self, drone_id: str) -> None:
        self.drone_id = drone_id

    @staticmethod
    def deserialize(
        payload: bytes, offset: int = 0
    ) -> tuple[int, "ConfirmRegistration"]:
        drone_id = struct.unpack_from("!4s", payload)[0].decode("utf-8")
        offset += 4
        return (offset, ConfirmRegistration(drone_id))

    def serialize(self) -> bytes:
        return struct.pack("!4s", self.drone_id)
