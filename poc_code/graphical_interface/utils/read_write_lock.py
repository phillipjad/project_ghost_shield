from threading import Condition, Lock


class RWLock:
    def __init__(self) -> None:
        self._readers = 0
        self._cv = Condition(Lock())

    def acquire_read(self) -> None:
        self._cv.acquire()
        try:
            while self._readers < 0:
                self._cv.wait()
            self._readers += 1
        finally:
            self._cv.release()

    def release_read(self) -> None:
        self._cv.acquire()
        try:
            self._readers -= 1
            if self._readers == 0:
                self._cv.notify_all()
        finally:
            self._cv.release()

    def acquire_write(self) -> None:
        self._cv.acquire()
        try:
            while self._readers != 0:
                self._cv.wait()
            self._readers = -1
        finally:
            self._cv.release()

    def release_write(self) -> None:
        self._cv.acquire()
        try:
            self._readers += 1
            self._cv.notify_all()
        finally:
            self._cv.release()
