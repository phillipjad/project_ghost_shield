from .msg_obj_abc import MsgObject


class CommandAck(MsgObject):
    @staticmethod
    def deserialize(payload: bytes | None = None, offset: int = 0) -> tuple[int, "CommandAck"]:
        return (offset, CommandAck())

    def serialize(self) -> bytes:
        return b""
