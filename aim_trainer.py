from ursina import *

from ursina.prefabs.first_person_controller import FirstPersonController

app = Ursina()

ground = Entity(model='plane', collider='box', scale=100, texture='grass', texture_scale=(4, 4))
sky = Sky()

Enemies = []
for i in range(10):
    Enemies.append(Entity(collider = 'sphere',model='sphere', color=color.blue, position=(random.randint(-10, 10), random.randint(1, 10), random.randint(-10, 10))))

player = FirstPersonController()

crosshair = Entity(parent=camera.ui, model='quad', scale=0.01, color=color.black)

def input(key):
    # Detect shooting (left mouse button click)
    if key == 'e':
        
        # Shoot the raycast from the camera's world position 
        hit_info = raycast(
            origin=camera.world_position, 
            direction=camera.forward, 
            distance=30, 
            ignore=(player,), # Don't hit yourself!
            debug=True        
        )
        
        # Check if the raycast hit an object with a collider
        if hit_info.hit:
            print(f"Hit object: {hit_info.entity}")
            
            if hit_info.entity in Enemies:
                print("Enemy hit!")
                hit_info.entity.color = color.yellow

app.run()