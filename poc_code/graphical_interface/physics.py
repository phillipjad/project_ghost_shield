from ursina import *


class PhysicsComponent:
    """
    General physics component that can be applied to any entity
    Handles gravity, collisions, and basic movement physics
    """

    def __init__(self, entity, gravity=0.8):
        self.entity = entity
        self.gravity = gravity
        self.velocity = Vec3(0, 0, 0)
        self.grounded = False
        self.affected_by_gravity = True

    def update(self, dt):
        """Update physics for this entity"""
        # Apply gravity if entity is affected by it and not grounded
        if self.affected_by_gravity and not self.grounded:
            self.velocity.y -= self.gravity * dt

            # Check for ground beneath
            hit_info = raycast(
                self.entity.position,
                direction=Vec3(0, -1, 0),
                distance=0.5,
                ignore=[self.entity]
            )

            if hit_info.hit:
                # Entity hit ground
                self.grounded = True
                self.velocity.y = 0
                # Place exactly on ground with slight offset to prevent clipping
                self.entity.y = hit_info.world_point.y + 0.1
            else:
                # Not on ground
                self.grounded = False

        # Apply velocity to position
        self.entity.position += self.velocity * dt

    def set_velocity(self, velocity):
        """Set the entity's velocity"""
        if isinstance(velocity, tuple):
            self.velocity = Vec3(*velocity)
        else:
            self.velocity = velocity

    def add_force(self, force, dt):
        """Add a force to current velocity"""
        if isinstance(force, tuple):
            force = Vec3(*force)
        self.velocity += force * dt

    def set_gravity_enabled(self, enabled):
        """Enable or disable gravity for this entity"""
        self.affected_by_gravity = enabled
        if not enabled:
            self.grounded = False
