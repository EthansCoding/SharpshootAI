from ursina import *

from ursina.prefabs.first_person_controller import FirstPersonController

class aim_trainer:

    def __init__(self, render_mode=None):
        self.render_mode = render_mode

        window_type = 'onscreen' if render_mode == "human" else 'none'
        self.app = Ursina(
            launch_ui=False,
            window_type=window_type,
            development_mode=False
        )

        self.input_handler = Entity(
            input=self.handle_input,
            ignore_paused=True
        )

        if self.render_mode == "human":
            self.ground = Entity(model='plane', collider='box', scale=100, texture='grass', texture_scale=(4, 4))
            self.sky = Sky()
        
            self.Enemies = []

            self.Enemies.append(Entity(collider = 'sphere',model='sphere', color=color.blue, position=(random.randint(-10, 10), random.randint(1, 10), random.randint(-10, 10))))
            self.Enemies[0].health = 3
        
            self.player = FirstPersonController()
        
            self.crosshair = Entity(parent=camera.ui, model='quad', scale=0.01, color=color.black)
        else:
            self.Enemies = []
            self.Enemies.append(Entity(collider = 'sphere', position=(random.randint(-10, 10), random.randint(1, 10), random.randint(-10, 10))))
            self.Enemies[0].health = 3
            
            self.player = Entity()
            self.player.camera_pivot = Entity(parent=self.player, y=2)

    def step(self):
        self.app.step()

    def start(self):
        self.app.run()

    def reset(self, render_mode=None):
        self.__init__(self.render_mode)

    def handle_input(self, key="none"):
        if key == 'escape':
            application.quit()

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