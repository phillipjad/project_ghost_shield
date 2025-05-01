from threading import Condition, Lock


class RWLock:
    """A read-write lock implementation that allows multiple readers or a single writer.

    This class provides methods to acquire and release read and write locks.
    """    
    def __init__(self) -> None:
        """Initializes the read-write lock.

        The lock is initialized with a reader count of 0 and a condition variable for synchronization.
        """        
        self._readers = 0
        self._cv = Condition(Lock())

    def acquire_read(self) -> None:
        """Acquires a read lock.

        This method blocks if there are active writers. It increments the reader count
        """        
        self._cv.acquire()
        try:
            while self._readers < 0:
                self._cv.wait()
            self._readers += 1
        finally:
            self._cv.release()

    def release_read(self) -> None:
        """Releases a read lock.

        This method decrements the reader count and notifies any waiting writers if there are no more readers.
        """        
        self._cv.acquire()
        try:
            self._readers -= 1
            if self._readers == 0:
                self._cv.notify_all()
        finally:
            self._cv.release()

    def acquire_write(self) -> None:
        """Acquires a write lock.

        This method blocks if there are active readers or writers. It sets the reader count to -1
        """        
        self._cv.acquire()
        try:
            while self._readers != 0:
                self._cv.wait()
            self._readers = -1
        finally:
            self._cv.release()

    def release_write(self) -> None:
        """Releases a write lock.
        
        This method resets the reader count to 0 and notifies all waiting readers and writers.
        """        
        self._cv.acquire()
        try:
            self._readers += 1
            self._cv.notify_all()
        finally:
            self._cv.release()
