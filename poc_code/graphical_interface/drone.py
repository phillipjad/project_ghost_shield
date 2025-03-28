from physics import DronePhysics
from ursina import *

class GUIDrone:
    def __init__(self, model_path: str, color: str = color.white, starter_position: tuple = (0, 5, 0), scale: float = 0.5):
        self.model_path = model_path
        self.color = color
        self.starter_position = starter_position
        self.scale = scale
        self.drone_entity = None
        self.physics = None

    def create_drone(self):
        try:
            self.drone_entity = Entity(
                model=self.model_path,
                texture='white',
                position=self.starter_position,
                scale=self.scale,
                color=self.color,
                collider='box'  # Add collider for physics interactions
            )
            # Create and attach physics behavior
            self.physics = DronePhysics(self.drone_entity)
            self.drone_entity.physics = self.physics
            print("Drone model loaded successfully!")
            return self.drone_entity
        except Exception as e:
            print(f"Error creating drone: {e}")
            self.drone_entity = Entity(
                model='cube',
                color=self.color,
                position=self.starter_position,
                scale=(0.8, 0.2, 0.8),
                collider='box'  # Add collider for physics interactions
            )
            # Create and attach physics behavior
            self.physics = DronePhysics(self.drone_entity)
            self.drone_entity.physics = self.physics
            print("Fallback to basic drone shape")
            return self.drone_entity

    def get_drone(self):
        return self.drone_entity
