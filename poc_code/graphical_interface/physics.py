from ursina import *

class DronePhysics:
    def __init__(self, entity):
        self.entity = entity
        self.gravity = 0.8
        self.velocity = Vec3(0, 0, 0)
        self.grounded = False

    def update(self):
        # Apply gravity if not on ground
        if not self.grounded:
            self.velocity.y -= self.gravity * time.dt

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
        self.entity.position += self.velocity * time.dt
