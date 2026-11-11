from ursina import *
from ursina.prefabs.first_person_controller import FirstPersonController
import datetime

'''
Aim Trainer game. It creates a 3D environment where a player can shoot at enemies.
The game can be created in 3 different ways. 
1. Human mode. - Creates a 3D environment where a human can play the game and move and shoot.
2. Playback mode. - Creates a 3D environment where the game can be played back with a camera and crosshair but no player movement.
3. Logic only mode. - Creates a 3D environment where the game logic is executed without any visual rendering.
'''
class aim_trainer:
    '''
    Aim Trainer initialization. It creates a 3D environment where a player can shoot at enemies.
    render_mode: str - The mode of the game. It can be "human", "playback" or None. If it is None, the game will be created in logic only mode.
    '''
    def __init__(self, render_mode=None):
        self.render_mode = render_mode

        #This section either creates or doesn't create a window and launches the app.
        window_type = 'onscreen' if render_mode in ["human", "playback"] else 'none'
        self.app = Ursina(
            launch_ui=False,
            window_type=window_type,
            development_mode=False,
            borderless=False,
            fullscreen=False,
            size=(1920, 1080)
        )

        #This section creates an input handler that listens for key presses and calls the handle_input method.
        self.input_handler = Entity(
            input=self.handle_input,
            ignore_paused=True
        )

        self.killCount = 0
        self.killTimes = []

        self.idle_texture = load_texture('assets/textures/first-person-pistol.png')
        self.fire_texture = load_texture('assets/textures/first-person-pistol-fire.png')

        #Depending on input mode the game render different important pieces.
        if self.render_mode == "human":
            self.renderScene() #Only render scene for humans and playback
        
            self.player = FirstPersonController() #First person controller includes movement.
            self.player.cursor.enabled = False

            self.gunshot = Audio(
                            'assets/gunshot.wav',
                            autoplay=False,
                            auto_destroy=False,
                            volume=0.7
                        )

            self.gun = Entity(
                            parent=camera.ui,
                            model='quad',
                            texture=self.idle_texture,
                            position=(.45, -.3),
                            scale=(.5, .4)
                        )
            self.crosshair = Entity(parent=camera.ui, model='quad', scale=0.01, color=color.black)
        elif self.render_mode == "playback":
            self.renderScene() #Only render scene for humans and playback
        
            self.player = Entity() #Use entity and no FPS controller on playback
            self.player.camera_pivot = Entity(parent = self.player, y=2)

            camera.parent = self.player.camera_pivot
            camera.position = (0, 0, 0)
            camera.rotation = (0, 0, 0)
            camera.fov = 90

            self.gunshot = Audio(
                'assets/gunshot.wav',
                autoplay=False,
                auto_destroy=False,
                volume=0.7
            )

            self.gun = Entity(
                parent=camera.ui,
                model='quad',
                texture=self.idle_texture,
                position=(.45, -.3),
                scale=(.5, .4)
            )
            self.crosshair = Entity(parent=camera.ui, model='quad', scale=0.01, color=color.black)
        else:
            self.player = Entity() #Use just entity and pivot for logic only headless
            self.player.camera_pivot = Entity(parent=self.player, y=2)

        #Always need enemies
        self.startEnemies()

    def step(self):
        self.app.step()

    def start(self):
        self.app.run()

    def close(self):
        application.quit()

    '''
    Reset the game state.
    '''
    def reset(self):
        for enemy in self.Enemies:
            destroy(enemy)
        self.startEnemies()

        self.killCount = 0
        self.killTimes = []
        if self.render_mode is not None:
            self.killCountText.text = f"Kills: {self.killCount}"
            self.avgKillTimeText.text = "Average Kill Time: 0.00s"
        
        self.player.camera_pivot.rotation = (0, 0, 0)

    '''
    Handle input if the game is being played by a smooth ML model.
    '''
    def smooth_input(self, input=(0, 0, 0)):
        self.player.camera_pivot.rotation_y += input[0]
        self.player.camera_pivot.rotation_x += input[1]
        if input[2] >= 0:
            self.shoot()

    '''
    Handle input if the game is being played by a simple ML model.
    Or a human player.
    '''
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
            self.shoot()
            
    '''
    Shoot a ray from the player's camera and check if it hits an enemy.
    If it does, reduce the enemy's health and update the kill count and average kill time.
    '''
    def shoot(self):
        hit_info = raycast(
            origin=self.player.camera_pivot.world_position, 
            direction=self.player.camera_pivot.forward, 
            distance=30, 
            ignore=(self.player,) # Don't hit yourself!
        )

        self.gun.texture = self.fire_texture
        self.gunshot.play()
        invoke(self.reset_gun, delay=0.5)
        
        # Check if the raycast hit an object with a collider
        if hit_info.hit:
            if hit_info.entity in self.Enemies:
                hit_info.entity.health -= 1
                if hit_info.entity.health <= 0:
                    self.killCount += 1
                    self.killTimes.append(datetime.datetime.now())
                    if self.render_mode is not None:
                        self.killCountText.text = f"Kills: {self.killCount}"
                        if len(self.killTimes) > 1:
                            durations = [
                                (self.killTimes[i] - self.killTimes[i - 1]).total_seconds()
                                for i in range(1, len(self.killTimes))
                            ]
                            average = sum(durations) / len(durations) if durations else 0
                        else: average = 0
                        self.avgKillTimeText.text = f"Average Kill Time: {average:.2f}s"
                    destroy(hit_info.entity)
                    self.Enemies.remove(hit_info.entity)
                    self.addEnemy()

    '''
    Add a new enemy to the game at a random position.
    '''
    def addEnemy(self):
        new_enemy = Entity(collider='sphere', model='sphere', texture='verity', position=(random.randint(-10, 10), random.randint(1, 10), random.randint(-10, 10)))
        new_enemy.health = 3
        new_enemy.look_at(self.player)
        new_enemy.texture_offset = (-0.25, 0)
        self.Enemies.append(new_enemy)

    '''
    Render the game scene with ground, walls, sky, and UI elements for kill count and average kill time.
    '''
    def renderScene(self):
        self.ground = Entity(model='plane', collider='box', scale=100, texture='bricks', texture_scale=(50, 50))
        Walls = []
        Walls.append(Entity(model='cube',collider='box',scale=(22, 10, 0.2),texture='planks',texture_scale=(11,5),position=(0,0,-11)))
        Walls.append(Entity(model='cube',collider='box',scale=(22, 10, 0.2),texture='planks',texture_scale=(11,5),position=(0,0,11)))
        Walls.append(Entity(model='cube',collider='box',scale=(.2, 10, 22),texture='planks',texture_scale=(11,5),position=(-11,0,0)))
        Walls.append(Entity(model='cube',collider='box',scale=(.2, 10, 22),texture='planks',texture_scale=(11,5),position=(11,0,0)))
        self.sky = Sky(texture="sky", model='sphere', double_sided=True, texture_scale=(1,1))
        self.killCount = 0
        self.killCountText = Text(text=f"Kills: {self.killCount}",font = "Avara.ttf", position=(-0.85, 0.45), scale=2, color=color.black)
        self.killTimes = []
        self.avgKillTimeText = Text(text="Average Kill Time: 0.00s",font = "Avara.ttf", position=(-0.85, 0.4), scale=2, color=color.black)

    '''
    Start the enemies list and add the first enemy to the game.
    '''
    def startEnemies(self):
        self.Enemies = []
        self.addEnemy()

    def reset_gun(self):
        self.gun.texture = self.idle_texture