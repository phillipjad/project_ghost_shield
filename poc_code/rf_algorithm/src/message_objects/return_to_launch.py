from .msg_obj_abc import MsgObject


class ReturnToLaunch(MsgObject):
    @staticmethod
    def deserialize(payload: bytes | None = None, offset: int = 0) -> tuple[int, "ReturnToLaunch"]:
        return (offset, ReturnToLaunch())

    def serialize(self) -> bytes:
        return b""
