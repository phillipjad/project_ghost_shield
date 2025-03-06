from utils.vector import Vector


class Drone:
    """Class representing a rudimentary drone. Capable of moving and broadcasting location"""

    def __init__(
        self, id: str, x_coordinate: float, y_coordinate: float, z_coordinate: float
    ) -> None:
        self.id = id
        self.x = x_coordinate
        self.y = y_coordinate
        self.z = z_coordinate

    def move_x(self, distance: float) -> None:
        self.x += distance

    def move_y(self, distance: float) -> None:
        self.y += distance

    def move_z(self, distance: float) -> None:
        self.z += distance

    def move_from_vector(self, vector: Vector) -> None:
        # check if vector has exactly 3 components
        # checks if there should be no movement at all
        if vector.get_magnitude() == 0.0:
            print("No movement")
            return

        vector_components = vector.get_internals_as_tuple()

        # print the movement vector
        print(
            f"Moving {self.pretty_print()} by x: {vector_components[0]}, y: {vector_components[1]}, z: {vector_components[2]}"
        )
        
        # moves the drone in the x, y, and z directions
        self.move_x(vector_components[0])
        self.move_y(vector_components[1])
        self.move_z(vector_components[2])

    def set_x(self, x: float) -> None:
        self.x = x

    def set_y(self, y: float) -> None:
        self.y = y
    
    def set_z(self, z: float) -> None:
        self.z = z

    def get_x(self) -> float:
        return self.x

    def get_y(self) -> float:
        return self.y

    def get_z(self) -> float:
        return self.z

    def get_id(self) -> str:
        return self.id


    def pretty_print(self) -> str:
        return f"Drone {self.id}"

    def __str__(self) -> str:
        return f"""
            Drone {self.id}
            X Coordinate: {self.x}
            Y Coordinate: {self.y}
            Z Coordinate: {self.z}
        """

    def __repr__(self) -> str:
        return f"ID: {self.id}\nX: {self.x}\nY: {self.y}\nZ: {self.z}\n"


if __name__ == "__main__":
    print("testing move_from_vector() method: ")

    # Create two drone instances
    drone1 = Drone("Alpha", 0.0, 0.0, 0.0)
    drone2 = Drone("Beta", 3.0, 4.0, 0.0)

    print("printing drone1 and drone2 before moving: ")
    print(drone1)
    print(drone2)
    print()

    # Move the first drone
    drone1.move_from_vector(Vector(-1.0, -1.0, -2.0))

    # Move the second drone
    drone2.move_from_vector(Vector(3.0, -6.0, 2.0))

    print()
    print("printing drone1 and drone2 after moving: ")
    print(drone1)
    print(drone2)
    print()

    # Calculate distance between them
    drone_1_vec = Vector(drone1.get_x(), drone1.get_y(), drone1.get_z())
    drone_2_vec = Vector(drone2.get_x(), drone2.get_y(), drone2.get_z())
    distance = drone_1_vec.distance_between_vector(drone_2_vec)
    print(f"Distance between drones: {distance}")
