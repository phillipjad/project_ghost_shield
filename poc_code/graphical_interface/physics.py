from ursina import *


class PhysicsComponent:
    """Simplified physics component for drones and other objects"""

    def __init__(self, entity, gravity=9.8):
        self.entity = entity
        self.gravity = gravity
        self.velocity = Vec3(0, 0, 0)
        self.grounded = False
        self.affected_by_gravity = True

        # Drone properties (13.5 pounds ≈ 6.12 kg)
        self.mass = 6.12

        # Lift properties
        self.lift_force = False

        hit_info = raycast(
            entity.position,
            direction=Vec3(0, -1, 0),
            distance=0.5,
            ignore=[entity]
        )
        self.grounded = hit_info.hit and entity.y <= hit_info.world_point.y + 0.1

        if self.grounded:
            entity.y = hit_info.world_point.y
            self.velocity = Vec3(0, 0, 0)



        self.max_lift = 15.0  # Maximum lift force - higher than gravity for good acceleration

        # Simple altitude control
        self.target_altitude = None
        self.vertical_speed = 3.0  # Vertical movement speed

        # PID controller parameters for altitude
        self.kp = 2.0  # Proportional gain
        self.kd = 1.5  # Derivative gain
        self.prev_error = 0  # Previous error for derivative calculation
        self.max_thrust = 20.0  # Maximum thrust force

    def update(self, dt):
        """Update physics for this entity"""
        # Apply gravity when not on ground
        if self.affected_by_gravity and not self.grounded:
            self.velocity.y -= self.gravity * dt

        # Handle lift for drone when motors active
        if self.lift_force:
            # If we have a target altitude, move toward it
            if self.target_altitude is not None:
                # Calculate error (distance from target)
                error = self.target_altitude - self.entity.y

                # Calculate error derivative (rate of change)
                error_derivative = (
                    error - self.prev_error) / dt if dt > 0 else 0
                self.prev_error = error

                # Calculate PID control output (simplified without integral term)
                # Base thrust counters gravity
                thrust = self.gravity

                # Add proportional component (responds to distance from target)
                thrust += error * self.kp

                # Add derivative component (responds to velocity - provides damping)
                thrust += error_derivative * self.kd

                # Limit thrust to reasonable values
                thrust = max(0, min(thrust, self.max_thrust))

                # Apply the calculated thrust
                self.velocity.y += thrust * dt
            else:
                # No target altitude, just hover
                self.velocity.y += self.gravity * dt

            # Once motors are active, we're not grounded
            self.grounded = False

        # Apply basic air resistance for stability
        self.velocity *= 0.99

        # Check for ground beneath
        hit_info = raycast(
            self.entity.position,
            direction=Vec3(0, -1, 0),
            distance=0.5,
            ignore=[self.entity]
        )

        if hit_info.hit:
            # Calculate how close we are to the ground
            ground_distance = self.entity.y - hit_info.world_point.y
            
            if ground_distance < 0.2 and self.velocity.y <= 0:  # Close to ground and moving down
                self.grounded = True
                self.velocity.y = 0
                
                # Only adjust position if we're actually below or too far above ground
                if ground_distance < 0 or ground_distance > 0.1:
                    self.entity.y = hit_info.world_point.y
        else:
            # Only unground if actually falling and no ground detected
            if self.grounded and self.velocity.y < 0:
                self.grounded = False

        # Apply velocity to position
        self.entity.position += self.velocity * dt

    def set_velocity(self, velocity):
        """Set entity's velocity"""
        if isinstance(velocity, tuple):
            self.velocity = Vec3(*velocity)
        else:
            self.velocity = velocity

    def add_force(self, force, dt):
        """Add a force to velocity"""
        if isinstance(force, tuple):
            force = Vec3(*force)
        self.velocity += force * dt

    def set_gravity_enabled(self, enabled):
        """Enable/disable gravity"""
        self.affected_by_gravity = enabled

    def enable_lift_force(self, target_altitude=None):
        """Start drone motors and set initial target altitude
        
        Args:
            target_altitude: Optional specific altitude to target, if None, no change to target
        """
        self.lift_force = True
        
        if target_altitude is not None:
            self.target_altitude = target_altitude

    def disable_lift_force(self):
        """Begin landing by setting target to ground level"""
        # Find ground below
        hit_info = raycast(
            self.entity.position,
            direction=Vec3(0, -1, 0),
            distance=100,
            ignore=[self.entity]
        )

        if hit_info.hit:
            self.target_altitude = hit_info.world_point.y + 0.1
        else:
            # No ground detected, just cut motors
            self.lift_force = False
            self.target_altitude = None
