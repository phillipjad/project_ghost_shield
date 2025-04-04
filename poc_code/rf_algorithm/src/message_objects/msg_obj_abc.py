from abc import ABC, abstractmethod

class MsgObject(ABC):

    @staticmethod
    @abstractmethod
    def deserialize(payload: bytes, offset: int = 0) -> tuple[int, "MsgObject"]:
        pass

    @abstractmethod
    def serialize(self) -> bytes:
        pass