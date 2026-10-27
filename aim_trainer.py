from ursina import *

from ursina.prefabs.first_person_controller import FirstPersonController

class aim_trainer:

    def __init__(self, render_mode=None):
        self.app = Ursina(launch_ui=False)

        self.input_handler = Entity(
            input=self.handle_input,
            ignore_paused=True
        )

        if render_mode != "human":
            window.visible = False
        
        self.ground = Entity(model='plane', collider='box', scale=100, texture='grass', texture_scale=(4, 4))
        self.sky = Sky()
    
        self.Enemies = []

        self.Enemies.append(Entity(collider = 'sphere',model='sphere', color=color.blue, position=(random.randint(-10, 10), random.randint(1, 10), random.randint(-10, 10))))
        self.Enemies[0].health = 3
    
        self.player = FirstPersonController()
    
        self.crosshair = Entity(parent=camera.ui, model='quad', scale=0.01, color=color.black)

    def step(self):
        self.app.step()

    def start(self):
        self.app.run()

    def handle_input(self, key="none"):
        if key == 'escape':
            self.app.quit()

        if key == 'right arrow':
            self.player.camera_pivot.rotation_y += 1

        if key == 'left arrow':
            self.player.camera_pivot.rotation_y -= 1

        if key == 'up arrow':
            self.player.camera_pivot.rotation_x -= 1

        if key == 'down arrow':
            self.player.camera_pivot.rotation_x += 1

        # Detect shooting (left mouse button click)
        if key == 'e':
            
            # Shoot the raycast from the camera's world position 
            hit_info = raycast(
                origin=self.player.camera_pivot.world_position, 
                direction=self.player.camera_pivot.forward, 
                distance=30, 
                ignore=(self.player,), # Don't hit yourself!
                debug=True        
            )
            
            # Check if the raycast hit an object with a collider
            if hit_info.hit:
                print(f"Hit object: {hit_info.entity}")
                
                if hit_info.entity in self.Enemies:
                    hit_info.entity.health -= 1
                    if hit_info.entity.health <= 0:
                        print("Enemy defeated!")
                        destroy(hit_info.entity)
                        self.Enemies.remove(hit_info.entity)
                        self.addEnemy()
    def addEnemy(self):
        new_enemy = Entity(collider='sphere', model='sphere', color=color.blue, position=(random.randint(-10, 10), random.randint(1, 10), random.randint(-10, 10)))
        new_enemy.health = 3
        self.Enemies.append(new_enemy)

aim_trainer_instance = aim_trainer("human")
aim_trainer_instance.start()