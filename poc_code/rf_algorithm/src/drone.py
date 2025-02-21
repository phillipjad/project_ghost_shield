import math


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
    
    def move_from_vector(self, vector: tuple[float, float, float]):
        #check if vector has exactly 3 components
        if len(vector) != 3:
            raise ValueError("Vector must have exactly three components (x, y, z).")
        
        #print the movement vector
        print(f"Moving {self.pretty_print()} by x: {vector[0]}, y: {vector[1]}, z: {vector[2]}")
        
        #checks if there should be no movement at all
        if(vector[0] == 0 and vector[1] == 0 and vector[2] == 0):
            print("No movement")
            
        #moves the drone in the x, y, and z directions
        else:
            self.move_x(vector[0])
            self.move_y(vector[1])
            self.move_z(vector[2])
        
    def get_x(self) -> float:
        return self.x

    def get_y(self) -> float:
        return self.y

    def get_z(self) -> float:
        return self.z

    def get_id(self) -> str:
        return self.id

    def calc_distance_between_drones(self, other: "Drone") -> int | float:
        return math.sqrt(
            math.pow((other.get_x() - self.get_x()), 2)
            + math.pow((other.get_y() - self.get_y()), 2)
            + math.pow(other.get_z() - self.get_z(), 2),
        )

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
    drone1.move_from_vector((-1.0, -1.0, -2.0))
    
    # Move the second drone
    drone2.move_from_vector((3.0, -6.0, 2.0))

    print()
    print("printing drone1 and drone2 after moving: ")
    print(drone1)
    print(drone2)
    print()

    # Calculate distance between them
    distance = drone1.calc_distance_between_drones(drone2)
    print(f"Distance between drones: {distance}")
