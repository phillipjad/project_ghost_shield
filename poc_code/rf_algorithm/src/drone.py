import math

class Drone:
    """Class representing a rudimentary drone. Capable of moving and broadcasting location"""
    def __init__(self, id: str, x_coordinate: float, y_coordinate: float, z_coordinate: float) -> None:
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

    def get_x(self) -> float:
        return self.x
    
    def get_y(self) -> float:
        return self.y
    
    def get_z(self) -> float:
        return self.z
    
    def get_id(self) -> str:
        return self.id

    def calc_distance_between_drones(self, other: "Drone") -> int | float:
        return math.sqrt(math.pow(((other.get_x() - self.get_x()) + (other.get_y() - self.get_y()) + (other.get_z() - self.get_z())), 2))
    
    def __str__(self) -> str:
        return f"""
            Drone {self.id}
            X Coordinate: {self.x}
            Y Coordinate: {self.y}
            Z Coordinate: {self.z}
        """

    def __repr__(self) -> str:
        return f"ID: {self.id}\nX: {self.x}\nY: {self.y}\nZ: {self.z}\n"