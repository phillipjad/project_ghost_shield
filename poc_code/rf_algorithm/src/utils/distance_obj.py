from copy import copy

from .read_write_lock import RWLock
from .vector import Vector


class Distance:
    def __init__(
        self, x: float, y: float, z: float, mutex: RWLock, last_to_write: int = -1
    ) -> None:
        self.vector = Vector(x, y, z)
        self.mutex = mutex
        self.last_to_write = last_to_write

    def get_vector(self) -> Vector:
        """Thread-safe way to acquire a copy of the internal distance vector.

        Returns:
            Vector: Internal vector representing distance between
            two nodes in the system.
        """
        self.mutex.acquire_read()
        vector = copy(self.vector)
        self.mutex.release_read()

        return vector

    def get_vector_abs(self) -> Vector:
        """Thread-safe way to acquire internal distance vector with absolute value applied.

        Returns:
            Vector: Internal vector representing absolute distance between
            two nodes in the system.
        """
        self.mutex.acquire_read()
        vector_abs = self.vector.as_abs()
        self.mutex.release_read()

        return vector_abs

    def get_vector_magnitutde(self) -> float:
        """Thread-safe way to calculate magnitude of internal vector.

        Returns:
            float: Magnitude of internal vector.
        """
        self.mutex.acquire_read()
        vector_magnitude = self.vector.get_magnitude()
        self.mutex.release_read()
        return vector_magnitude

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
        self.vector._update_vector(x=x, y=y, z=z)
        self.last_to_write = drone_id
        self.mutex.release_write()

    def update_vector_with_vector(self, vector: Vector, drone_id: int) -> None:
        """Thread-safe way to update internal distance vector.

        Args:
            vector Vector: New vector to update internal instance variable
            with.
        """
        self.mutex.acquire_write()
        self.vector._replace_internals_with_vector(vector)
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

    def distance_between_vectors(self, other_vector: Vector) -> float:
        """Calculates the distance between the calling vector and another vector.

        Args:
            other_vector (Vector): Other distance vector to use in distance measurement.

        Returns:
            float: Distance between the points represented by the two position vectors.
        """
        self.mutex.acquire_read()
        distance = self.vector.distance_between_vector(other_vector)
        self.mutex.release_read()

        return distance

    def distance_between_vectors_using_abs(self, other_vector: Vector) -> float:
        """Calculates the distance between the absolute value representation of the calling vector and another vector

        Args:
            other_vector (Vector): Other distance vector to use in distance measurement.

        Returns:
            float: Distance between the points represented by the two position vectors.
        """
        self.mutex.acquire_read()
        distance = self.vector.as_abs().distance_between_vector(other_vector)
        self.mutex.release_read()

        return distance

    def __str__(self) -> str:
        self.mutex.acquire_read()
        vector_internals = self.vector.get_internals_as_tuple()
        self.mutex.release_read()

        return f"<{vector_internals[0]}, {vector_internals[1]}, {vector_internals[2]}>"
