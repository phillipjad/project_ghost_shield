from .msg_obj_abc import MsgObject


class GetLocation(MsgObject):
    @staticmethod
    def deserialize(payload: bytes | None = None, offset: int = 0) -> tuple[int, "GetLocation"]:
        return (offset, GetLocation())

    def serialize(self) -> bytes:
        return b""
