from ursina import *
import numpy as np

app = Ursina()

# Create terrain with varying height
terrain = Entity(model='terrain', scale=(20, 5, 20),
                 collider='mesh', texture='grass')

# Create object to place on terrain
box = Entity(model='cube', color=color.orange, position=(0, 10, 0))

# Store terrain heights in a dictionary for faster lookup
terrain_heights = {}


def get_terrain_height(x, z):
    # Check if we've already calculated this position
    key = (round(x, 1), round(z, 1))
    if key in terrain_heights:
        return terrain_heights[key]

    # Cast ray to find terrain height
    ray = raycast(Vec3(x, 100, z), Vec3(0, -1, 0),
                  distance=200, traverse_target=terrain)
    if ray.hit:
        terrain_heights[key] = ray.world_point.y
        return ray.world_point.y
    return 0


def calculate_surface_normal(position, sample_distance=0.5):
    # Get heights at nearby points
    center = get_terrain_height(position.x, position.z)
    right = get_terrain_height(position.x + sample_distance, position.z)
    forward = get_terrain_height(position.x, position.z + sample_distance)

    # Calculate terrain tangent vectors
    tangent1 = Vec3(sample_distance, right - center, 0)
    tangent2 = Vec3(0, forward - center, sample_distance)

    # Calculate normal using cross product
    normal = tangent1.cross(tangent2)
    normal.normalize()
    return normal


def update():
    # Apply gravity
    terrain_y = get_terrain_height(box.x, box.z)
    target_y = terrain_y + box.scale_y/2

    if box.y > target_y:
        # Object is above ground, apply gravity
        box.y -= 9.8 * time.dt
        if box.y < target_y:
            box.y = target_y  # Don't sink below ground
    else:
        # Object is at or below ground level
        box.y = target_y

        # Align to surface normal
        normal = calculate_surface_normal(box.position)
        up_vector = Vec3(0, 1, 0)

        # Create rotation to align with surface normal
        if normal != up_vector:
            rotation_axis = up_vector.cross(normal)
            rotation_axis.normalize()
            dot_product = min(1.0, max(-1.0, up_vector.dot(normal)))
            rotation_angle = math.acos(dot_product)
            box.rotation = (
                rotation_axis.x * rotation_angle * 57.2957795,  # Convert to degrees
                box.rotation.y,
                rotation_axis.z * rotation_angle * 57.2957795
            )

app.run()
