import math
from utils.read_write_lock import RWLock


class Distance:
    def __init__(
        self, x: float, y: float, z: float, mutex: RWLock, last_to_write: int = -1
    ) -> None:
        self.vector = (x, y, z)
        self.mutex = mutex
        self.last_to_write = last_to_write

    def get_vector(self) -> tuple[float, float, float]:
        """Thread-safe way to acquire internal distance vector.

        Returns:
            tuple[float, float, float]: Internal vector representing distance between
            two nodes in the system.
        """
        self.mutex.acquire_read()
        vector = self.vector
        self.mutex.release_read()

        return vector
    
    def get_vector_abs(self) -> tuple[float, float, float]:
        """Thread-safe way to acquire internal distance vector with absolute value applied.

        Returns:
            tuple[float, float, float]: Internal vector representing absolute distance between
            two nodes in the system.
        """
        self.mutex.acquire_read()
        tmp_vec = self.vector
        vector_abs = (abs(tmp_vec[0]), abs(tmp_vec[1]), abs(tmp_vec[2]))
        self.mutex.release_read()

        return vector_abs

    def get_vector_magnitutde(self) -> float:
        """Thread-safe way to calculate magnitude of internal vector.

        Returns:
            float: Magnitude of internal vector.
        """
        self.mutex.acquire_read()
        vector = self.vector
        self.mutex.release_read()
        return math.sqrt((vector[0] ** 2) + (vector[1] ** 2) + (vector[2] ** 2))

    def update_vector_with_coords(
        self, x: float, y: float, z: float, drone_id: int
    ) -> None:
        """Thread-safe way to update internal distance vector.

        Args:
            x (float): New x coordinate.
            y (float): New y coordinate.
            z (float): New z coordinate.
        """
        self.mutex.acquire_write()
        self.vector = (x, y, z)
        self.last_to_write = drone_id
        self.mutex.release_write()

    def update_vector_with_vector(
        self, vector: tuple[float, float, float], drone_id: int
    ) -> None:
        """Thread-safe way to update internal distance vector.

        Args:
            vector (tuple[float, float, float]): New vector to update internal instance variable
            with.
        """
        self.mutex.acquire_write()
        self.vector = vector
        self.last_to_write = drone_id
        self.mutex.release_write()

    def get_rwlock(self) -> RWLock:
        """Getter for internal RWLock.

        Returns:
            RWLock: Returns the RW that this Distance object was instantiated with.
        """
        return self.mutex

    def get_last_to_write(self) -> int:
        """Getter for last to write.

        Returns:
            int: Drone id of the last drone to update distance.
        """
        self.mutex.acquire_read()
        drone_id = self.last_to_write
        self.mutex.release_read()

        return drone_id

    @staticmethod
    def distance_between_vectors(vec_1: tuple[float, float, float], vec_2: tuple[float, float, float]) -> float | int:
        """Calculates the distance between two position vectors.

        Args:
            vec_1 (tuple[float, float, float]): First position vector in the form tuple[x, y, z].
            vec_2 (tuple[float, float, float]): Second position vector in the form tuple[x, y, z].

        Returns:
            float | int: Distance between the points represented by the two position vectors.
        """
        return math.sqrt(
            math.pow(vec_2[0] - vec_1[0], 2)
            + math.pow(vec_2[1] - vec_1[1], 2)
            + math.pow(vec_2[2] - vec_1[2], 2),
        )

    def __str__(self) -> str:
        self.mutex.acquire_read()
        vector = self.vector
        self.mutex.release_read()

        return f"<{vector[0]}, {vector[1]}, {vector[2]}>"
