from .msg_obj_abc import MsgObject


class JammerEnabled(MsgObject):
    @staticmethod
    def deserialize(payload: bytes | None = None, offset: int = 0) -> tuple[int, "JammerEnabled"]:
        return (offset, JammerEnabled())

    def serialize(self) -> bytes:
        return b""
