from ursina import *
from physics import PhysicsComponent
import random
import math


class GUIDrone:
    def __init__(self, starter_position, model_path='models/drone.glb', color=color.white, scale=0.5, takeoff_delay=float('inf')):
        # Basic properties
        self.model_path = model_path
        self.color = color
        self.starter_position = starter_position
        self.scale = scale

        # Start on ground - ground surface varies with terrain
        # Use x,z from starter_position, but place on ground level
        ground_position = Vec3(starter_position[0], 0, starter_position[2])

        # Create the drone entity
        self.drone_entity = Entity(
            model=self.model_path,
            texture='white',
            position=ground_position,
            scale=self.scale,
            color=self.color
        )

        # Cast a ray from high above the object straight down
        ray_start = Vec3(self.drone_entity.x, 100, self.drone_entity.z)
        ray_direction = Vec3(0, -1, 0)
        ray_distance = 200

        # Find the ground height
        hit_info = raycast(ray_start, ray_direction, distance=ray_distance)

        if hit_info.hit:
            # Set y position to the exact ground height
            ground_height = hit_info.world_point.y
            
            # Handle the specific case where ground is at y=0
            if abs(ground_height) < 0.001:  # Small threshold for floating point precision
                ground_height = 0
                
            self.drone_entity.y = ground_height
        else:
            # Fallback if no ground detected
            self.drone_entity.y = 0

        # Add physics component
        self.physics = PhysicsComponent(self.drone_entity)

        # Movement parameters
        self.target_position = None
        self.max_speed = 5.0
        self.acceleration = 2.0
        self.is_moving = False
        self.velocity = Vec3(0, 0, 0)
        self.physics.lift_force = False
        # Takeoff parameters
        self.took_off = False
        self.takeoff_timer = 0
        self.takeoff_delay = takeoff_delay

    def update(self, dt):
        """Update drone movement each frame"""
        if not self.drone_entity:
            return

        if self.physics.lift_force:
            # Make sure we respect that we're trying to take off
            self.took_off = True
            # IMPORTANT: Always update physics when motors are active
            self.physics.update(dt)
        elif self.took_off:
            # Already flying, update physics
            self.physics.update(dt)
        else:
            # Still on ground, just do ground check
            hit_info = raycast(
                self.drone_entity.position,
                direction=Vec3(0, -1, 0),
                distance=0.5,
                ignore=[self.drone_entity]
            )
            if hit_info.hit:
                self.drone_entity.y = hit_info.world_point.y
                self.physics.velocity = Vec3(0, 0, 0)
                self.physics.grounded = True

        # Handle initial waiting period and takeoff
            if not self.took_off:
                self.takeoff_timer += dt
                if self.takeoff_timer >= self.takeoff_delay and not self.is_moving:
                    # Use starter position's y as target
                    self.physics.enable_lift_force(self.starter_position[1])
                    self.move_to(self.starter_position)
                    self.took_off = True
            if self.is_moving:  # Still process movement if an external command set it
                pass  # Continue to movement logic below
            else:
                return  # Only return if we're not moving

        if self.took_off and not self.is_moving:
            # Apply hover effects when flying but not actively moving
            self.apply_hover_effects(dt)
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

            # Smooth acceleration (for horizontal movement only)
            target_velocity = Vec3(
                direction.x * target_speed,
                0,  # Don't modify Y velocity, handled by physics
                direction.z * target_speed
            )

            # Update horizontal velocity components
            self.velocity.x = lerp(
                self.velocity.x, target_velocity.x, min(1.0, self.acceleration * dt))
            self.velocity.z = lerp(
                self.velocity.z, target_velocity.z, min(1.0, self.acceleration * dt))

            # Apply horizontal velocity to physics component
            self.physics.velocity.x = self.velocity.x
            self.physics.velocity.z = self.velocity.z
        else:
            # Reached target position
            self.is_moving = False
            # Apply small hover effects instead of freezing
            self.apply_hover_effects(dt)

            # Ensure we're mostly at the target position (horizontally)
            # But allow slight drift for realism
            self.drone_entity.x = lerp(
                self.drone_entity.x, self.target_position.x, 0.1)
            self.drone_entity.z = lerp(
                self.drone_entity.z, self.target_position.z, 0.1)

    def apply_hover_effects(self, dt):
        """Apply realistic hover effects to make the drone feel alive"""
        # Add small random movements to simulate air disturbances
        random_force = Vec3(
            (random.random() - 0.5) * 0.3,  # Increased x disturbance
            (random.random() - 0.5) * 0.2,  # Increased y disturbance
            (random.random() - 0.5) * 0.3   # Increased z disturbance
        )

        # Apply the small random force
        self.physics.add_force(random_force, dt)

        # Dampen horizontal velocity for stability (but don't eliminate it)
        self.physics.velocity.x *= 0.95
        self.physics.velocity.z *= 0.95

        # Keep motors active to counteract gravity
        self.physics.lift_force = True

        # This is key: Continuously vary the target altitude slightly
        # This creates a natural hovering effect
        if self.physics.target_altitude is not None:
            # Create a small sinusoidal variation to the hover height
            self.hover_time = getattr(self, 'hover_time', 0) + dt
            # Subtle vertical oscillation
            hover_offset = math.sin(self.hover_time * 1.5) * 0.1

            # If we have a target position, vary around that target height
            if self.target_position:
                self.physics.target_altitude = self.target_position.y + hover_offset
            else:
                # Otherwise, vary around current height
                self.physics.target_altitude = self.drone_entity.y + hover_offset

    def move_to(self, position, delay=0):
        """Move drone to the specified position after optional delay

        Args:
            position: Target position as (x,y,z) tuple or Vec3
            delay: Time in seconds to wait before executing the movement (default: 0)
        """
        if delay > 0:
            # Schedule the movement using Ursina's invoke function
            invoke(lambda: self._execute_move_to(position), delay=delay)
            return True

        # If no delay, execute immediately
        return self._execute_move_to(position)

    def _execute_move_to(self, position):
        """Internal method that performs the actual movement logic"""
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

        # Set target altitude for vertical movement
        self.physics.target_altitude = position.y

        # Ensure motors are active when moving
        if not self.physics.lift_force:
            self.physics.enable_lift_force()

        return True

    def rotate_to(self, rotation):
        """Rotate drone to specified rotation (x, y, z)"""
        if not self.drone_entity:
            return False

        if isinstance(rotation, tuple):
            self.drone_entity.rotation = rotation
        return True

    def take_off(self):
        """Explicitly start the drone motors for takeoff"""
        self.took_off = True
        
        # Use the starter position's y-value as the target altitude
        target_y = self.starter_position[1] if self.starter_position else None
        self.physics.enable_lift_force(target_y)
        
        # If we have a starter position, move to it
        if self.starter_position:
            self._execute_move_to(self.starter_position)

    def land(self):
        """Begin landing sequence"""
        self.physics.disable_lift_force()
