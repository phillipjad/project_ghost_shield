from ursina import *
from ursina.prefabs.ursfx import ursfx
from physics import PhysicsComponent
import random
import math


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
            color=self.color,
            collision_type='sphere',  # Add collision detection
            collider='sphere',         # Add collider for collision detection
            radius=0.5                 # Set collision radius explicitly
        )

        # Place drone on ground surface using ray casting
        hit_info = raycast(self.drone_entity.position +
                           Vec3(0, 100, 0), Vec3(0, -1, 0), distance=200)
        if hit_info.hit:
            # Set y position to actual ground height
            self.drone_entity.y = hit_info.world_point.y

        # Add physics component
        self.physics = PhysicsComponent(self.drone_entity)

        # Movement parameters
        self.target_position = None
        self.max_speed = 5.0
        self.acceleration = 2.0
        self.is_moving = False
        self.velocity = Vec3(0, 0, 0)

        # Rotation parameters
        self.rotation_speed = 3.0  # Speed at which drone rotates to face direction
        self.tilt_factor = 10.0    # How much the drone tilts during movement
        # Target rotation (pitch, yaw, roll)
        self.target_rotation = Vec3(0, 0, 0)

        # Takeoff parameters
        self.took_off = False
        self.takeoff_timer = 0
        self.takeoff_delay = 5  # Wait 5 seconds before taking off

        # Crash parameters
        self.crashed = False
        self.fire_entity = None
        self.falling_speed = 0
        self.collision_cooldown = 0  # Prevents multiple collisions

        # Register collision event handler
        self.drone_entity.on_collision = self.on_collision

    def update(self, dt):
        """Update drone movement each frame"""
        if not self.drone_entity:
            return

        # Update physics (handles gravity and lift)
        self.physics.update(dt)

        # Handle collision cooldown
        if self.collision_cooldown > 0:
            self.collision_cooldown -= dt

        # If crashed, handle crash behavior
        if self.crashed:
            self._handle_crash(dt)
            return

        # Check for coordinate-based collisions with other drones
        if not self.crashed and self.collision_cooldown <= 0:
            self._check_drone_collisions()

        # Handle initial waiting period and takeoff
        if not self.took_off:
            self.takeoff_timer += dt
            if self.takeoff_timer >= self.takeoff_delay and not self.is_moving:
                self.physics.take_off()  # Activate motors for takeoff
                self.move_to(self.starter_position)
                self.took_off = True
            if self.is_moving:  # Still process movement if an external command set it
                pass  # Continue to movement logic below
            else:
                return  # Only return if we're not moving

        if not self.is_moving:
            # Even when not actively moving to a target, apply hover effects
            self.apply_hover_effects(dt)

            # When not moving, gradually level out the drone
            self._smooth_rotate_to(
                Vec3(0, self.drone_entity.rotation.y, 0), dt, recovery=True)
            return

        # Calculate vector to target
        to_target = self.target_position - self.drone_entity.position
        distance = to_target.length()

        if distance > 0.1:  # Still moving toward target
            # Calculate direction and speed
            direction = to_target.normalized()

            # Calculate target yaw (rotation around Y-axis) based on movement direction
            # atan2 gives us the angle in radians, convert to degrees
            target_yaw = math.degrees(
                math.atan2(direction.z, direction.x)) - 90

            # Calculate pitch and roll based on acceleration and movement
            # Tilt forward in the direction of movement
            horizontal_speed = Vec3(
                self.velocity.x, 0, self.velocity.z).length()
            target_pitch = -direction.z * horizontal_speed * self.tilt_factor
            target_roll = direction.x * horizontal_speed * self.tilt_factor

            # Clamp tilt values to reasonable amounts
            target_pitch = max(-15, min(15, target_pitch))
            target_roll = max(-15, min(15, target_roll))

            # Set target rotation
            target_rotation = Vec3(target_pitch, target_yaw, target_roll)

            # Smoothly rotate to face direction of travel
            self._smooth_rotate_to(target_rotation, dt)

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
        self.physics.motors_active = True

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
        # Don't accept new movement commands if crashed
        if self.crashed:
            return False

        if delay > 0:
            # Schedule the movement using Ursina's invoke function
            invoke(lambda: self._execute_move_to(position), delay=delay)
            return True

        # If no delay, execute immediately
        return self._execute_move_to(position)

    def _execute_move_to(self, position):
        """Internal method that performs the actual movement logic"""
        if not self.drone_entity or self.crashed:
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
        if not self.physics.motors_active:
            self.physics.take_off()

        return True

    def rotate_to(self, rotation):
        """Rotate drone to specified rotation (x, y, z)"""
        if not self.drone_entity or self.crashed:
            return False

        if isinstance(rotation, tuple):
            self.drone_entity.rotation = rotation
        return True

    def take_off(self):
        """Explicitly start the drone motors for takeoff"""
        if not self.crashed:
            self.physics.take_off()

    def land(self):
        """Begin landing sequence"""
        if not self.crashed:
            self.physics.land()

    def _smooth_rotate_to(self, target_rotation, dt, recovery=False):
        """Smoothly interpolate current rotation to target rotation

        Args:
            target_rotation: The target rotation as Vec3(pitch, yaw, roll)
            dt: Delta time for frame-rate independent rotation
            recovery: If True, use a faster rotation speed for recovery to level
        """
        if not self.drone_entity:
            return

        # Convert target rotation to Vector3
        if isinstance(target_rotation, tuple):
            target_rotation = Vec3(*target_rotation)

        # Store the target for debugging/other functions
        self.target_rotation = target_rotation

        # Use faster rotation for recovery (stabilizing after movement)
        rotation_speed = self.rotation_speed * 2 if recovery else self.rotation_speed

        # Smoothly interpolate current rotation to target rotation
        # Note: Need to handle yaw angle wrapping around 360 degrees
        current_rotation = self.drone_entity.rotation

        # Handle the special case of yaw (y-rotation) which can wrap around
        # Find the shortest direction to rotate (clockwise or counter-clockwise)
        current_yaw = current_rotation.y % 360
        target_yaw = target_rotation.y % 360
        delta_yaw = target_yaw - current_yaw

        # Handle the case where rotating the other direction is shorter
        if delta_yaw > 180:
            delta_yaw -= 360
        elif delta_yaw < -180:
            delta_yaw += 360

        # Calculate new rotation values
        new_pitch = lerp(current_rotation.x, target_rotation.x,
                         min(1.0, rotation_speed * dt))
        new_yaw = (current_yaw + delta_yaw *
                   min(1.0, rotation_speed * dt)) % 360
        new_roll = lerp(current_rotation.z, target_rotation.z,
                        min(1.0, rotation_speed * dt))

        # Apply new rotation
        self.drone_entity.rotation = Vec3(new_pitch, new_yaw, new_roll)


    def on_collision(self, other_entity):
        """Handle collision with another entity"""
        # Ignore if already crashed or if collision cooldown active
        if self.crashed or self.collision_cooldown > 0:
            return

        # Check if collided with another drone
        if hasattr(other_entity, 'model') and 'drone' in str(other_entity.model).lower():
            print(
                f"[Collision Detected] {self.drone_entity} collided with {other_entity}")

            self.crash()
            self.collision_cooldown = 1.0  # Prevent repeated collision triggers


    def crash(self):
        """Crash the drone and add fire effect"""
        if self.crashed:
            return

        self.crashed = True
        self.is_moving = False

        # IMPORTANT: Completely disable motors and set all vertical control to null
        self.physics.motors_active = False
        self.physics.target_altitude = None

        # Instead of resetting vertical velocity to zero, add some downward momentum
        # This helps the drone immediately start falling instead of floating up
        # Force initial downward velocity
        self.physics.velocity.y = min(
            self.physics.velocity.y, -5.0)  # Strong downward force


        # Ensure gravity is explicitly enabled
        self.physics.affected_by_gravity = True

        # Reduce horizontal velocity but not to zero (for momentum)
        self.physics.velocity.x *= 0.2
        self.physics.velocity.z *= 0.2

        # Create fire effect using fire.obj
        self.fire_entity = Entity(
            model='models/fire.obj',
            scale=0.3,
            color=color.orange,
            position=self.drone_entity.position + Vec3(0, 0.1, 0),
            billboard=True  # Fire always faces camera
        )

        # Change drone color to indicate damage
        self.drone_entity.color = color.rgb(100, 100, 100)  # Darkened color

        print(f"Drone crashed at position {self.drone_entity.position}")

    def _handle_crash(self, dt):
        """Handle crash behavior - directly apply gravity to make drone fall"""
        if not self.crashed or not self.drone_entity:
            return

        # Directly apply gravity to make sure drone falls
        # Don't rely on physics component which might have conflicting behavior
        self.physics.velocity.y -= self.physics.gravity * \
            dt * 1.2  # Slightly stronger gravity for quick fall

        # Cap falling speed (terminal velocity)
        self.physics.velocity.y = max(self.physics.velocity.y, -10.0)

        # Add random tumbling rotation to simulate loss of control
        self.drone_entity.rotation_x += random.uniform(-50, 50) * dt
        self.drone_entity.rotation_z += random.uniform(-50, 50) * dt

        # Check if drone hit the ground - USE LONGER DISTANCE FOR RELIABLE DETECTION
        hit_info = raycast(
            self.drone_entity.position + Vec3(0, 0.1, 0),
            Vec3(0, -1, 0),
            distance=1.0  # Increased from 0.2 to 1.0 for better ground detection
        )

        # If on ground, stop the drone
        if hit_info.hit or self.drone_entity.y <= 0.1:
            # Drone hit the ground - stop all movement
            self.drone_entity.y = max(
                0.1, hit_info.world_point.y if hit_info.hit else 0.1)
            self.physics.velocity = Vec3(0, 0, 0)

            # IMPORTANT: Set grounded state to ensure it stays down
            self.physics.grounded = True

            # Prevent any future lift by ensuring motors stay off
            self.physics.motors_active = False
            self.physics.target_altitude = None

            # Add a final crashed rotation
            if not hasattr(self, 'crash_landed'):
                self.crash_landed = True
                self.drone_entity.rotation = Vec3(
                    random.uniform(-30, 45),
                    self.drone_entity.rotation.y,
                    random.uniform(-30, 45)
                )

        # Update fire position to follow the drone
        if self.fire_entity:
            self.fire_entity.position = self.drone_entity.position + \
                Vec3(0, 0.1, 0)

    def _check_drone_collisions(self):
        """Check for collisions with other drones based on coordinates"""
        if not hasattr(GUIDrone, 'all_drones') or not GUIDrone.all_drones:
            return

        # Don't check if we're already crashed
        if self.crashed:
            return

        # Get current drone position
        my_pos = self.drone_entity.position

        # Check distance to all other drones
        for other_drone in GUIDrone.all_drones:
            # Skip self
            if other_drone == self:
                continue

            # Skip already crashed drones
            if other_drone.crashed:
                continue

            # Get other drone position
            other_pos = other_drone.drone_entity.position

            # Calculate distance between drones
            distance = (my_pos - other_pos).length()

            # If drones are very close or at the same position (within a small threshold)
            # The threshold is smaller than the physical size to ensure they need to be very close
            if distance < 1.0:  # Close enough to be considered a collision
                print(
                    f"Collision detected between drones at positions: {my_pos} and {other_pos}")
                # Crash both drones
                self.crash()
                other_drone.crash()
                return


# Class variable to track all drones for collision detection
GUIDrone.all_drones = []