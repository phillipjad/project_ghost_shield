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
        self.motors_active = False
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

        # Apply gravity explicitly if drone not grounded
        if self.affected_by_gravity and not self.grounded:
            self.velocity.y -= self.gravity * dt

        # ONLY apply thrust if motors active and target altitude exists
        if self.motors_active and self.target_altitude is not None:
            error = self.target_altitude - self.entity.y
            error_derivative = (error - self.prev_error) / dt if dt > 0 else 0
            self.prev_error = error

            thrust = self.gravity
            thrust += error * self.kp
            thrust += error_derivative * self.kd
            thrust = max(0, min(thrust, self.max_thrust))

            self.velocity.y += thrust * dt
        else:
            # Reset PID errors explicitly when motors are off
            self.prev_error = 0

        # Air resistance
        self.velocity *= 0.99

        # Ground collision detection
        hit_info = raycast(
            self.entity.position,
            direction=Vec3(0, -1, 0),
            distance=0.5,
            ignore=[self.entity]
        )

        if hit_info.hit and self.velocity.y <= 0:
            self.grounded = True
            self.velocity.y = 0
            self.entity.y = hit_info.world_point.y + 0.1
        else:
            self.grounded = False

        # Update position
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

    def take_off(self):
        """Start drone motors and set initial target altitude"""
        self.motors_active = True
        # Set target altitude 5 units above current ground position
        self.target_altitude = self.entity.y + 5.0

    def land(self):
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
            self.motors_active = False
            self.target_altitude = None
