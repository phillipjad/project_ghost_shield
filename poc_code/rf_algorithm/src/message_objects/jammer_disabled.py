from .msg_obj_abc import MsgObject


class JammerDisabled(MsgObject):
    @staticmethod
    def deserialize(payload: bytes | None = None, offset: int = 0) -> tuple[int, "JammerDisabled"]:
        return (offset, JammerDisabled())

    def serialize(self) -> bytes:
        return b""
