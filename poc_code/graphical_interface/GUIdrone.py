from ursina import *

class GUIDrone:
    def __init__(self, starter_position, model_path='models/drone.glb', color=color.white, scale=0.5):
        # Basic properties
        self.model_path = model_path
        self.color = color
        self.starter_position = starter_position
        self.scale = scale
        self.drone_entity = Entity(
            model=self.model_path,
            texture='white',
            position=self.starter_position,
            scale=self.scale,
            color=self.colorz
        )

        # Movement parameters
        self.target_position = None
        self.max_speed = 5.0
        self.acceleration = 2.0
        self.is_moving = False
        self.velocity = Vec3(0, 0, 0)

    def update(self, dt):
        """Update drone movement each frame"""
        if not self.drone_entity or not self.is_moving:
            return

        # Calculate vector to target
        to_target = self.target_position - self.drone_entity.position
        distance = to_target.length()

        if distance > 0.1:  # Still moving toward target
            # Calculate direction and speed
            direction = to_target.normalized()

            # Start fast, slow down when approaching the target
            target_speed = min(self.max_speed, distance)
            if distance < 2.0:
                target_speed *= (distance / 2.0)

            # Smooth acceleration
            target_velocity = direction * target_speed
            self.velocity = lerp(self.velocity, target_velocity, min(
                1.0, self.acceleration * dt))

            # Apply movement
            self.drone_entity.position += self.velocity * dt
        else:
            # Reached target position
            self.is_moving = False
            self.velocity = Vec3(0, 0, 0)
            # Ensure we're exactly at the target position
            self.drone_entity.position = self.target_position

    def move_to(self, position):
        """Move drone to the specified position"""
        if not self.drone_entity:
            return False

        # Handle different position input formats
        if isinstance(position, tuple):
            if len(position) == 2:  # (x,z) format
                x, z = position
                y = self.drone_entity.y  # Keep current height
                position = Vec3(x, y, z)
            else:  # (x,y,z) format
                position = Vec3(*position)

        # Set target and start movement
        self.target_position = position
        self.is_moving = True
        return True

    def rotate_to(self, rotation):
        """Rotate drone to specified rotation (x, y, z)"""
        if not self.drone_entity:
            return False

        if isinstance(rotation, tuple):
            self.drone_entity.rotation = rotation
        return True
