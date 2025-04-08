from .msg_obj_abc import MsgObject


class EnableRegistration(MsgObject):

    def __init__(self, _: bytes | None) -> None:
        super.__init__()
    
    @staticmethod
    def deserialize(
        payload: bytes | None = None, offset: int = 0
    ) -> tuple[int, "EnableRegistration"]:
        return (offset, EnableRegistration())

    def serialize(self) -> bytes:
        return b""
