from ursina import *


class GUIDrone:
    def __init__(self, starter_position, model_path='models/drone.glb', color=color.white, scale=1, takeoff_delay=0):
        self.model_path = model_path
        self.color = color
        self.starter_position = starter_position
        self.scale = scale
        self.move_queue = []
        self.move_cooldown = 0
        self.takeoff_delay = takeoff_delay
        self.time_since_start = 0
        self.move_speed = 3  # Units per second

        # Find terrain height at (x,z) position using raycasting
        x, y, z = starter_position

        # Start ray high above terrain and cast down
        ray_height = 100  # Start ray from high up
        ray_origin = Vec3(x, ray_height, z)
        ray_direction = Vec3(0, -1, 0)  # Cast straight down

        # Perform the raycast, only targeting the terrain
        hit_info = raycast(ray_origin, ray_direction, distance=ray_height*2)

        # Ensure a minimum height offset to prevent sinking
        min_height_offset = 0.2  # Increased from 0.5 to 1.5

        if hit_info.hit:
            terrain_height = hit_info.world_point.y
            ground_y = terrain_height + min_height_offset
            print(
                f"Drone at ({x}, {y}, {z}): Terrain height = {terrain_height}, Placing at {ground_y}")
        else:
            # Fallback with a safe height
            # Use at least 2 units, or the original y if higher
            ground_y = max(2, y)
            print(
                f"Raycast failed for drone at ({x}, {y}, {z}). Using fallback height {ground_y}")

        # Position the drone at the safer ground position
        ground_position = Vec3(x, ground_y, z)

        self.drone_entity = Entity(
            model=self.model_path,
            texture='white',
            position=ground_position,
            scale=self.scale,
            color=self.color,
        )

        # For flight target, ensure minimum safe height
        if y != 0:
            # Ensure the target height is at least the ground height
            safe_y = max(y, ground_y)
            self.target_position = Vec3(x, safe_y, z)
            self.is_moving = True
        else:
            # Stay at ground height
            self.target_position = None
            self.is_moving = False

    def update(self, dt):
        self.time_since_start += dt
        if self.time_since_start < self.takeoff_delay:
            return  # Wait for takeoff delay

        # If the drone is moving toward a target
        if self.is_moving and self.target_position:
            current_pos = self.drone_entity.position
            target_pos = self.target_position

            # Calculate direction vector and distance
            direction = target_pos - current_pos
            distance = direction.length()

            # If we're close enough, snap to exact position
            if distance < 0.1:
                self.drone_entity.position = target_pos
                self.is_moving = False
                self.target_position = None

                # Process next item in queue if we have one
                if self.move_queue:
                    next_pos = self.move_queue.pop(0)
                    self.target_position = Vec3(*next_pos)
                    self.is_moving = True
            else:
                # Move toward target at constant speed
                move_step = min(self.move_speed * dt, distance)
                normalized_direction = direction.normalized()
                movement = normalized_direction * move_step
                self.drone_entity.position += movement

        # If we're not moving but have items in the queue, start moving to the next one
        elif not self.is_moving and self.move_queue:
            next_pos = self.move_queue.pop(0)
            self.target_position = Vec3(*next_pos)
            self.is_moving = True

    def move_to(self, position):
        # Add the position to the move queue
        self.move_queue.append(position)

        # If not currently moving, start moving immediately
        if not self.is_moving and not self.target_position:
            next_pos = self.move_queue.pop(0)
            self.target_position = Vec3(*next_pos)
            self.is_moving = True
