import math


class Vector:
    """Class representing distance vectors."""

    def __init__(self, x: float, y: float, z: float) -> None:
        self.x = x
        self.y = y
        self.z = z

    def __copy__(self) -> "Vector":
        """Returns a copy of this vector.

        Returns:
            Vector: Copy of calling vector.
        """
        return Vector(self.x, self.y, self.z)

    def as_abs(self) -> "Vector":
        """Returns a copy of this vector with all internal data set to their corresponding absolute value.

        Returns:
            Vector: Copy of the calling vector with all internal data set to their corresponding absolute value.
        """
        return Vector(abs(self.x), abs(self.y), abs(self.z))

    def get_magnitude(self) -> float:
        """Returns the magnitude of this vector.

        Returns:
            float: Magnitude of this vector.
        """
        return math.sqrt((self.x**2) + (self.y**2) + (self.z**2))

    def get_internals_as_tuple(self) -> tuple[float, float, float]:
        """Returns a tuple containing the class x, y, z variables in order.

        Returns:
            tuple[float, float, float]: A tuple containing the class x, y, z variables in order.
        """
        return (self.x, self.y, self.z)

    def _update_vector(
        self, *, x: float | None = None, y: float | None = None, z: float | None = None
    ) -> None:
        """Protected method to mutate the internal state of the calling vector.

        Args:
            x (float | None, optional): New x coordinate value. Defaults to None.
            y (float | None, optional): New y coordinate value. Defaults to None.
            z (float | None, optional): New z coordinate value. Defaults to None.
        """
        if x:
            self.x = x
        if y:
            self.y = y
        if z:
            self.z = z

    def _replace_internals_with_vector(self, vector: "Vector") -> None:
        """Protected method to mutate the internal state of the calling vector.

        Args:
            vector (Vector): Vector to mutate calling Vector object into.
        """
        replacement_values: tuple[float, float, float] = vector.get_internals_as_tuple()
        self.x = replacement_values[0]
        self.y = replacement_values[1]
        self.z = replacement_values[2]

    def distance_between_vector(self, other_vector: "Vector") -> float:
        """Calculates the distance between the tip of two position vectors.

        Args:
            other_vector (Vector): Other vector to use in distance formula.

        Returns:
            float: The distance between the tip of the calling and provided vector.
        """
        return math.sqrt(
            math.pow((other_vector.x - self.x), 2)
            + math.pow((other_vector.y - self.y), 2)
            + math.pow((other_vector.z - self.z), 2)
        )

    def vector_sum(self, other_vector: "Vector") -> "Vector":
        """Calculates the vector sum between the calling vector and the provided vector. Returns resultant as new Vector object.

        Args:
            other_vector (Vector): Additional Vector object to add to calling vector.

        Returns:
            Vector: Resultant of vector sum.
        """
        return Vector(
            self.x + other_vector.x, self.y + other_vector.y, self.z + other_vector.z
        )

    def mutating_vector_sum(self, other_vector: "Vector") -> None:
        """Mutates the internal state of the calling Vector by summing the
        internal components with the internal components of the provided Vector.

        Args:
            other_vector (Vector): Vector to sum with.
        """
        self.x += other_vector.x
        self.y += other_vector.y
        self.z += other_vector.z

    def as_negated(self) -> "Vector":
        """Returns the vector with all components negated.

        Returns:
            Vector: A vector with all internal components of the calling vector negated.
        """
        return Vector((-1 * self.x), (-1 * self.y), (-1 * self.z))

    def calculate_force(
        self, min_distance: float, repulsion_strength: float
    ) -> "Vector":
        """Calculates a force vector based on the calling Vector's internal state,
        and a passed repulsion_strength. min_distance parameter ensures that at least
        a minimal change occurs.

        Args:
            min_distance (float): Minimum distance that distance should be calculated as.
            repulsion_strength (float): Strength of repulsive force.

        Returns:
            Vector: Force vector calculated from the calling Vector's internal state and the provided repulsion_strength parameter.
        """
        inner_components: tuple[float, float, float] = self.get_internals_as_tuple()
        distance = max(min_distance, self.get_magnitude())

        # calculate the force between the drones the formula is f = repulsion_strength / distance^2
        # the closer the 2 drones the stronger the force
        force = repulsion_strength / math.pow(distance, 2)

        return Vector(
            ((inner_components[0] / distance) * force),
            ((inner_components[1] / distance) * force),
            ((inner_components[2] / distance) * force),
        )
