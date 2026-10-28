from ursina import *

from ursina.prefabs.first_person_controller import FirstPersonController

class aim_trainer:

    def __init__(self, render_mode=None):
        self.render_mode = render_mode

        window_type = 'onscreen' if render_mode in ["human", "playback"] else 'none'
        self.app = Ursina(
            launch_ui=False,
            window_type=window_type,
            development_mode=False,
            borderless=False,
            fullscreen=False,
            size=(1920, 1080)
        )

        self.input_handler = Entity(
            input=self.handle_input,
            ignore_paused=True
        )

        self.killCount = 0

        if self.render_mode == "human":
            self.renderScene() #Only render scene for humans and playback
        
            self.player = FirstPersonController()
            self.player.cursor.enabled = False
        
            self.crosshair = Entity(parent=camera.ui, model='quad', scale=0.01, color=color.black)
        elif self.render_mode == "playback":
            self.renderScene() #Only render scene for humans and playback
        
            self.player = Entity() #Use entity and no FPS controller on playback
            self.player.camera_pivot = Entity(parent = self.player, y=2)

            camera.parent = self.player.camera_pivot
            camera.position = (0, 0, 0)
            camera.rotation = (0, 0, 0)
            camera.fov = 90
        
            self.crosshair = Entity(parent=camera.ui, model='quad', scale=0.01, color=color.black)
        else:
            self.player = Entity() #Use just entity and pivot for logic only headless
            self.player.camera_pivot = Entity(parent=self.player, y=2)

        self.startEnemies()

    def step(self):
        self.app.step()

    def start(self):
        self.app.run()

    def close(self):
        application.quit()
        
    def reset(self, render_mode=None):
        for enemy in self.Enemies:
            destroy(enemy)
        self.startEnemies()

        print(f"Kills since last reset: {self.killCount}")
        self.killCount = 0
        
        self.player.camera_pivot.rotation = (0, 0, 0)

    def handle_input(self, key="none"):
        if key == 'escape':
            self.close()

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
                ignore=(self.player,) # Don't hit yourself!
            )
            
            # Check if the raycast hit an object with a collider
            if hit_info.hit:
                
                if hit_info.entity in self.Enemies:
                    hit_info.entity.health -= 1
                    if hit_info.entity.health <= 0:
                        self.killCount += 1
                        destroy(hit_info.entity)
                        self.Enemies.remove(hit_info.entity)
                        self.addEnemy()

    def addEnemy(self):
        new_enemy = Entity(collider='sphere', model='sphere', texture='verity', position=(random.randint(-10, 10), random.randint(1, 10), random.randint(-10, 10)))
        new_enemy.health = 3
        new_enemy.look_at(self.player)
        new_enemy.texture_offset = (-0.25, 0)
        self.Enemies.append(new_enemy)

    def renderScene(self):
        self.ground = Entity(model='plane', collider='box', scale=100, texture='bricks', texture_scale=(50, 50))
        Walls = []
        Walls.append(Entity(model='cube',collider='box',scale=(22, 10, 0.2),texture='planks',texture_scale=(11,5),position=(0,0,-11)))
        Walls.append(Entity(model='cube',collider='box',scale=(22, 10, 0.2),texture='planks',texture_scale=(11,5),position=(0,0,11)))
        Walls.append(Entity(model='cube',collider='box',scale=(.2, 10, 22),texture='planks',texture_scale=(11,5),position=(-11,0,0)))
        Walls.append(Entity(model='cube',collider='box',scale=(.2, 10, 22),texture='planks',texture_scale=(11,5),position=(11,0,0)))
        self.sky = Sky(texture="sky", model='sphere', double_sided=True, texture_scale=(1,1))

    def startEnemies(self):
        self.Enemies = []
        self.addEnemy()