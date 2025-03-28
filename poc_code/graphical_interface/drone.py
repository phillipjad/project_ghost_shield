from ursina import *
from physics import PhysicsComponent
import math


class GUIDrone:
    def __init__(self, model_path: str, color: str = color.white, starter_position: tuple = (0, 5, 0), scale: float = 0.5):
        self.model_path = model_path
        self.color = color
        self.starter_position = starter_position
        self.scale = scale
        self.drone_entity = None
        self.physics = None

        # Movement parameters
        self.target_position = None
        self.max_speed = 5.0
        self.acceleration = 2.0
        self.deceleration = 3.0
        self.hover_height = 0.1
        self.hover_timer = 0
        self.is_moving = False

    def create_drone(self):
        """Create the drone entity and attach physics"""
        try:
            self.drone_entity = Entity(
                model=self.model_path,
                texture='white',
                position=self.starter_position,
                scale=self.scale,
                color=self.color,
                collider='box'
            )
            # Create and attach physics component
            self.physics = PhysicsComponent(self.drone_entity)
            print("Drone model loaded successfully!")
            return self.drone_entity
        except Exception as e:
            print(f"Error creating drone: {e}")
            self.drone_entity = Entity(
                model='cube',
                color=self.color,
                position=self.starter_position,
                scale=(0.8, 0.2, 0.8),
                collider='box'
            )
            # Create and attach physics component
            self.physics = PhysicsComponent(self.drone_entity)
            print("Fallback to basic drone shape")
            return self.drone_entity

    def update(self, dt):
        """Update drone movement and behavior"""
        if not self.drone_entity or not self.physics:
            return

        # Only disable gravity when actively moving to a target
        if self.is_moving:
            self.physics.set_gravity_enabled(False)
        else:
            self.physics.set_gravity_enabled(True)

        self.hover_timer += dt

        # Handle movement if we have a target
        if self.is_moving and self.target_position:
            # Calculate vector to target
            to_target = self.target_position - self.drone_entity.position
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
                current_velocity = self.physics.velocity
                new_velocity = lerp(current_velocity, target_velocity,
                                    min(1.0, self.acceleration * dt))
                self.physics.set_velocity(new_velocity)

                # Apply visual tilting in movement direction
                self._update_visual_tilt(dt)
            else:
                # Reached target position
                self.is_moving = False

                # Hover in place
                hover_velocity = Vec3(0, math.sin(
                    self.hover_timer * 2) * self.hover_height, 0)
                self.physics.set_velocity(hover_velocity)

                # Reset rotation to level
                self._reset_rotation(dt)
        elif self.target_position:
            hover_velocity = Vec3(0, math.sin(self.hover_timer * 2) * self.hover_height, 0)
            self.physics.set_velocity(hover_velocity)

        self.physics.update(dt)

    def _update_visual_tilt(self, dt):
        """Update visual tilting based on movement direction"""
        velocity = self.physics.velocity

        if velocity.xz.length() > 0.1:
            # Tilt forward in direction of movement
            forward_tilt = min(
                30, velocity.y * -5) if velocity.y > 0 else min(15, velocity.xz.length() * 3)
            self.drone_entity.rotation_x = lerp(
                self.drone_entity.rotation_x, forward_tilt, 2 * dt)

            # Bank slightly into turns
            if abs(velocity.x) > 0.1:
                side_tilt = -velocity.x * 3
                self.drone_entity.rotation_z = lerp(
                    self.drone_entity.rotation_z, side_tilt, 2 * dt)

    def _reset_rotation(self, dt):
        """Gradually reset rotation to level"""
        self.drone_entity.rotation_x = lerp(
            self.drone_entity.rotation_x, 0, 3 * dt)
        self.drone_entity.rotation_z = lerp(
            self.drone_entity.rotation_z, 0, 3 * dt)

    def move_to(self, position):
        """
        Move drone to the specified position

        Parameters:
        - position: Target position as (x,y,z) or (x,z) tuple or Vec3
        """
        # Handle different position input formats
        if isinstance(position, tuple):
            if len(position) == 2:  # (x,z) format
                x, z = position
                # Get current height or some default height
                y = self.drone_entity.y + 5  # Move up by default
                position = Vec3(x, y, z)
            else:  # (x,y,z) format
                position = Vec3(*position)

        self.target_position = position
        self.is_moving = True

        # Disable gravity while moving (drone generates lift)
        self.physics.set_gravity_enabled(False)

        return True
