import struct

from msg_obj_abc import MsgObject

class EnableRegistration(MsgObject):

    @staticmethod
    def deserialize(payload: bytes, offset: int = 0) -> tuple[int, "EnableRegistration"]:
        return (offset, EnableRegistration())
    
    def serialize(self) -> bytes:
        return b''