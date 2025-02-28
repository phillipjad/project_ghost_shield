class Controller:
    def __init__(self, x: float, y: float, z: float) -> None:
        self.x = x
        self.y = y
        self.z = z

    def get_location(self) -> tuple[float, float, float]:
        return (self.x, self.y, self.z)