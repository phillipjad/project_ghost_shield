from ursina import *
from ursina.prefabs.first_person_controller import FirstPersonController
import math
import os

app = Ursina()
window.title = "3D Terrain with Drone"
window.borderless = False

mountain = Terrain(heightmap='topo1.png', skip=4)
terrain = Entity(model=mountain, scale=(10, 2, 10),
                 texture='topo1.png', collider='mesh')

safety_floor = Entity(
    model='plane',
    scale=(100, 1, 100),
    position=(0, -2, 0),
    collider='box',
    visible=False
)

player = FirstPersonController(y=10, position=(0, 10, 5))
player.scale = 0.5
player.gravity = 0.8
player.speed = 5
player.jump_height = 2
player.camera_pivot.y = 2

position_text = Text(text="", position=(-0.5, -0.4))

scene.ambient_light = color.rgba(0.8, 0.8, 0.8, 1)
model_path = 'model/drone.glb' 

try:
    print(f"Attempting to load drone model: {model_path}")
    print(f"Current working directory: {os.getcwd()}")
    
    drone_body = Entity(
        model=model_path,
        texture='white',
        position=(0, 7, -10),
        scale=0.5, 
        color=color.white
    )
    print("Drone model loaded successfully!")
    
    
except Exception as e:
    print(f"Error loading drone model: {e}")
    drone_body = Entity(
        model='cube',
        color=color.orange,
        position=(0, 7, -10),
        scale=(0.8, 0.2, 0.8)
    )
    print("Fallback to basic drone shape")

print(f"Drone created at position {drone_body.position}")

class Hovering(Entity):
    def __init__(self, entity_to_animate, hover_height=0.5, hover_speed=1):
        super().__init__()
        self.entity = entity_to_animate
        self.hover_height = hover_height
        self.hover_speed = hover_speed
        self.original_y = entity_to_animate.y
        self.t = 0
    
    def update(self):
        self.t += time.dt * self.hover_speed
        self.entity.y = self.original_y + math.sin(self.t) * self.hover_height
        position_text.text = f"Player: {player.position.Round()}\nDrone: {self.entity.position.Round()}"

drone_hover = Hovering(drone_body, hover_height=0.3, hover_speed=1.5)

class SafetyCheck(Entity):
    def update(self):
        if player.y < -10:
            player.y = 10
            print("Player reset due to falling through map")

safety = SafetyCheck()

instruction_text = Text(
    text="Use WASD to move, SPACE to jump\nArrow keys to move drone",
    position=(-0.5, 0.4),
    scale=1.5
)

def input(key):
    if key == 'right arrow':
        drone_body.x += 0.5
    if key == 'left arrow':
        drone_body.x -= 0.5
    if key == 'up arrow':
        drone_body.z -= 0.5
    if key == 'down arrow':
        drone_body.z += 0.5
    if key == 'page up':
        drone_body.y += 0.5
    if key == 'page down':
        drone_body.y -= 0.5

app.run()
