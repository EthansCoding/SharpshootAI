import gymnasium as gym
from gymnasium import spaces
import numpy as np
from aim_trainer import aim_trainer

class AimTrainerEnv(gym.Env):
    def __init__(self, render_mode=None):
        super().__init__()

        self.action_space = spaces.Discrete(5)  # 0: No action, 1: Move left, 2: Move right, 3: Move up, 4: Move down

        low = np.array([-1, -1, -1, -1], dtype=np.float32)
        high = np.array([1, 1, 1, 1], dtype=np.float32)
        self.observation_space = spaces.Box(low=low, high=high)

        self.aim_trainer_instance = aim_trainer()

    def reset(self):
        self.aim_trainer_instance.reset()

        return np.zeros(4, dtype=np.float32), {}

    def step(self, action):
        beforeXY, beforeZX = self.getAngleToEnemy()
        beforeDMG = self.aim_trainer_instance.enemies[0].health

        if action == 1:
            self.aim_trainer_instance.handle_input('left arrow')
        elif action == 2:
            self.aim_trainer_instance.handle_input('right arrow')
        elif action == 3:
            self.aim_trainer_instance.handle_input('up arrow')
        elif action == 4:
            self.aim_trainer_instance.handle_input('down arrow')
        elif action == 5:
            self.aim_trainer_instance.handle_input('e')
        self.aim_trainer_instance.step()

        thetaXY, thetaZX = self.getAngleToEnemy()

        reward = (abs(beforeXY) - abs(thetaXY)) + (abs(beforeZX) - abs(thetaZX)) * .05
        if beforeDMG != self.aim_trainer_instance.enemies[0].health:
            reward += 3

        observation = np.array([np.cos(thetaXY), np.sin(thetaXY), np.cos(thetaZX), np.sin(thetaZX)], dtype=np.float32)

        terminated = False
        truncated = False
        info = {}

        return (observation, reward, terminated, truncated, info)

    def getAngleToEnemy(self):
        position = self.aim_trainer_instance.enemies[0].world_position
        ownPosition = self.aim_trainer_instance.player.camera_pivot.world_position

        hypotenuseXY = ((position.x - ownPosition.x)**2 + (position.y - ownPosition.y)**2) ** .5
        thetaXY = np.arcsin((position.y - ownPosition.y) / hypotenuseXY)

        hypotenuseZX = ((position.z - ownPosition.z)**2 + (position.x - ownPosition.x)**2) ** .5
        thetaZX = np.arcsin((position.z - ownPosition.z) / hypotenuseZX)

        return thetaXY, thetaZX

    def close(self):
        self.aim_trainer_instance.app.quit()