from ursina import *
from physics import PhysicsComponent
import random
import math


class GUIDrone:
    def __init__(self, starter_position, model_path='models/drone.glb', color=color.white, scale=0.5, takeoff_delay=float('inf')):
        self.model_path = model_path
        self.color = color
        self.starter_position = starter_position
        self.scale = scale
        self.move_queue = []
        self.move_cooldown = 0

        # Start on ground - use x,z from starter_position, and raycast for ground y
        ground_position = Vec3(starter_position[0], 0, starter_position[2])


        self.drone_entity = Entity(
            model=self.model_path,
            texture='white',
            position=ground_position,
            scale=self.scale,
            color=self.color,
            collider='box'  # Add this line to create a collider
        )


        # Ground alignment
        ray_start = Vec3(self.drone_entity.x, 100, self.drone_entity.z)
        hit_info = raycast(ray_start, Vec3(0, -1, 0), distance=200)

        if hit_info.hit:
            ground_height = hit_info.world_point.y
            offset = self.scale * 0.5  # Raise it so it's not sunk into the ground
            self.drone_entity.y = ground_height + offset
        else:
            self.drone_entity.y = 0


        if hit_info.hit:
            ground_height = hit_info.world_point.y
            self.drone_entity.y = 0 if abs(ground_height) < 0.001 else ground_height
        else:
            self.drone_entity.y = 0

        self.physics = PhysicsComponent(self.drone_entity)

        self.target_position = None
        self.max_speed = 5.0
        self.acceleration = 2.0
        self.is_moving = False
        self.velocity = Vec3(0, 0, 0)
        self.physics.lift_force = False

        self.took_off = False
        self.takeoff_timer = 0
        self.takeoff_delay = takeoff_delay


    def update(self, dt):
        if not self.drone_entity:
            return

        if self.physics.lift_force:
            self.took_off = True
            self.physics.update(dt)
        elif self.took_off:
            self.physics.update(dt)
        else:
            hit_info = raycast(
                self.drone_entity.position,
                direction=Vec3(0, -1, 0),
                distance=0.5,
                ignore=[self.drone_entity]
            )
            if hit_info.hit:
                self.drone_entity.y = hit_info.world_point.y

            if not self.took_off:
                self.takeoff_timer += dt
                if self.takeoff_timer >= self.takeoff_delay and not self.is_moving:
                    if self.starter_position[1] > 0:
                        self.physics.enable_lift_force(self.starter_position[1])
                        self.move_to(self.starter_position)
                        self.took_off = True

            if not self.is_moving:
                return

        # === Handle move queue ===
        if not self.is_moving:
            if self.move_queue:
                if self.move_cooldown <= 0:
                    next_target = self.move_queue.pop(0)
                    self._execute_move_to(next_target)
                    self.move_cooldown = 3  # seconds between moves
                else:
                    self.move_cooldown -= dt
            else:
                return  # No moves pending

        # === Move towards current target ===
        if self.target_position:
            to_target = self.target_position - self.drone_entity.position
            distance = to_target.length()

            if distance > 0.1:
                direction = to_target.normalized()
                target_speed = min(self.max_speed, distance)
                if distance < 2.0:
                    target_speed *= (distance / 2.0)

                target_velocity = Vec3(
                    direction.x * target_speed,
                    0,
                    direction.z * target_speed
                )

                self.velocity.x = lerp(
                    self.velocity.x, target_velocity.x, min(1.0, self.acceleration * dt))
                self.velocity.z = lerp(
                    self.velocity.z, target_velocity.z, min(1.0, self.acceleration * dt))

                self.physics.velocity.x = self.velocity.x
                self.physics.velocity.z = self.velocity.z
            else:
                self.is_moving = False
                self.drone_entity.x = lerp(
                    self.drone_entity.x, self.target_position.x, 0.2)
                self.drone_entity.z = lerp(
                    self.drone_entity.z, self.target_position.z, 0.2)
                self.target_position = None



    def move_to(self, position):
        """Queue a move to the specified position (no manual delay needed)."""
        if isinstance(position, tuple):
            position = Vec3(*position)
        self.move_queue.append(position)


    def _execute_move_to(self, position):
        if not self.drone_entity:
            return False

        self.target_position = position
        self.is_moving = True
        self.physics.target_altitude = position.y

        if not self.physics.lift_force:
            print("Enabling lift force")
            self.physics.enable_lift_force()

        return True
    

    def check_collision(self, other_drone):
        """Check if this drone has the exact same coordinates as another drone"""
        if not self.drone_entity or not other_drone.drone_entity:
            return False

        # Get positions
        p1 = self.drone_entity.position
        p2 = other_drone.drone_entity.position

        # Check if coordinates are the same (with a small threshold for floating point precision)
        threshold = 0.1  # Small threshold for coordinate matching

        same_x = abs(p1.x - p2.x) < threshold
        same_y = abs(p1.y - p2.y) < threshold
        same_z = abs(p1.z - p2.z) < threshold

        # Collision occurs only when all coordinates match
        return same_x and same_y and same_z


    def handle_collision(self):
        """Handle collision by disabling lift and enabling gravity"""
        if self.physics.lift_force:
            print("Drone collision detected! Disabling lift force.")
            self.physics.lift_force = False
            self.physics.affected_by_gravity = True
            # Add slight randomness to fall direction so drones don't fall exactly the same way
            self.physics.velocity += Vec3(
                random.uniform(-0.5, 0.5),
                -0.5,  # Push it down a bit
                random.uniform(-0.5, 0.5)
            )
