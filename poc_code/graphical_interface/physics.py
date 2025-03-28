import math
import time
from ursina import *
class DronePhysics:
    def __init__(self, entity):
        self.entity = entity
        self.gravity = 0.8
        self.velocity = Vec3(0, 0, 0)
        self.grounded = False

        # Movement parameters
        self.target_position = None
        self.max_speed = 3.0
        self.acceleration = 1.5
        self.is_flying = False
        self.hover_height = 0.1
        self.hover_timer = 0

    def update(self):
        dt = time.dt
        self.hover_timer += dt

        if self.is_flying and self.target_position:
            # Calculate vector to target
            to_target = self.target_position - self.entity.position
            distance = to_target.length()

            if distance > 0.1:  # Still moving toward target
                # Normalize direction
                direction = to_target.normalized()

                # Calculate speed based on distance (accelerate/decelerate smoothly)
                target_speed = min(self.max_speed, distance)
                if distance < 3.0:  # Decelerate when approaching
                    target_speed *= distance / 3.0

                # Gradually adjust velocity (smoother acceleration)
                target_velocity = direction * target_speed
                self.velocity = lerp(self.velocity, target_velocity, min(
                    1.0, self.acceleration * dt))

                # Tilt slightly in direction of movement for realism
                if self.velocity.xz.length() > 0.1:
                    # Tilt forward in direction of movement
                    forward_tilt = min(
                        30, self.velocity.y * -5) if self.velocity.y > 0 else min(15, self.velocity.xz.length() * 3)
                    self.entity.rotation_x = lerp(
                        self.entity.rotation_x, forward_tilt, 2 * dt)

                    # Bank slightly into turns
                    if abs(self.velocity.x) > 0.1:
                        side_tilt = -self.velocity.x * 3
                        self.entity.rotation_z = lerp(
                            self.entity.rotation_z, side_tilt, 2 * dt)
            else:
                # Reached target, hover
                self.velocity = Vec3(0, math.sin(
                    self.hover_timer * 2) * self.hover_height, 0)

                # Gradually level out rotation
                self.entity.rotation_x = lerp(
                    self.entity.rotation_x, 0, 3 * dt)
                self.entity.rotation_z = lerp(
                    self.entity.rotation_z, 0, 3 * dt)

        elif not self.is_flying:
            # Apply gravity when not flying
            if not self.grounded:
                self.velocity.y -= self.gravity * dt

                # Check for ground beneath
                hit_info = raycast(
                    self.entity.position,
                    direction=Vec3(0, -1, 0),
                    distance=0.5,
                    ignore=[self.entity]
                )

                if hit_info.hit:
                    # We hit the ground, stop falling
                    self.grounded = True
                    self.velocity.y = 0
                    # Place exactly on ground with slight offset to prevent clipping
                    self.entity.y = hit_info.world_point.y + 0.1
                else:
                    # Keep falling
                    self.grounded = False

        # Apply velocity
        self.entity.position += self.velocity * dt

    def move_to(self, target_position):
        """Command the drone to move to a specific position"""
        if isinstance(target_position, tuple):
            target_position = Vec3(*target_position)
        self.target_position = target_position
        self.is_flying = True
        self.grounded = False
