from ursina import *


class GUIDrone:
    def __init__(self, drone_id, starter_position, model_path='models/drone.glb', color=color.white, scale=1):
        self.drone_id = drone_id
        self.model_path = model_path
        self.color = color
        self.starter_position = starter_position
        self.scale = scale
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
        else:
            # Fallback with a safe height
            # Use at least 2 units, or the original y if higher
            ground_y = max(2, y)

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
        if self.is_moving and self.target_position:
            cur = self.drone_entity.position
            dest = self.target_position
            gap = dest - cur
            dist = gap.length()

            if dist < 0.01:
                self.drone_entity.position = dest
                self.is_moving = False
                self.target_position = None
                return

            step_fraction = 0.009          # 10 % of the remaining gap each frame
            self.drone_entity.position += gap * step_fraction

    def move_to(self, position):
        x, y, z  = position

        # Clamp Y to terrain height if needed
        ray_origin = Vec3(x, 100, z)
        hit_info = raycast(ray_origin, Vec3(0, -1, 0), distance=200)

        min_offset = 0.2
        if hit_info.hit:
            terrain_y = hit_info.world_point.y
            y = max(y, terrain_y + min_offset)

        self.target_position = Vec3(x, z, y)
        self.is_moving = True
