from ursina import *


class GUIDrone:
    def __init__(self, starter_position, model_path='models/drone.glb', color=color.white, scale=0.5):
        # Basic properties
        self.model_path = model_path
        self.color = color
        self.starter_position = starter_position
        self.scale = scale

        # Start on ground - ground surface varies with terrain
        # Use x,z from starter_position, but place on ground level
        ground_position = Vec3(starter_position[0], 0, starter_position[2])

        self.drone_entity = Entity(
            model=self.model_path,
            texture='white',
            position=ground_position,  # Initial position on ground
            scale=self.scale,
            color=self.color
        )

        # Place drone on ground surface using ray casting
        hit_info = raycast(self.drone_entity.position +
                           Vec3(0, 100, 0), Vec3(0, -1, 0), distance=200)
        if hit_info.hit:
            # Set y position to actual ground height
            self.drone_entity.y = hit_info.world_point.y

        # Movement parameters
        self.target_position = None
        self.max_speed = 5.0
        self.acceleration = 2.0
        self.is_moving = False
        self.velocity = Vec3(0, 0, 0)

        # Takeoff parameters
        self.took_off = False
        self.takeoff_timer = 0
        self.takeoff_delay = 5  # Wait 2 seconds before taking off

    def update(self, dt):
        """Update drone movement each frame"""
        if not self.drone_entity:
            return

        # Handle initial waiting period and takeoff
        if not self.took_off:
            self.takeoff_timer += dt
            if self.takeoff_timer >= self.takeoff_delay and not self.is_moving:
                self.move_to(self.starter_position)
                self.took_off = True
            if self.is_moving:  # Still process movement if an external command set it
                pass  # Continue to movement logic below
            else:
                return  # Only return if we're not moving

        if not self.is_moving:
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
