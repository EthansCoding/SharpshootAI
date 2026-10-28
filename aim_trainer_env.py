import gymnasium as gym
from gymnasium import spaces
import numpy as np
from aim_trainer import aim_trainer

class AimTrainerEnv(gym.Env):
    def __init__(self, render_mode=None, movement_type="simple"):
        super().__init__()

        self.movement_type = movement_type
        if self.movement_type == "simple":
            self.action_space = spaces.Discrete(6)  # 0: No action, 1: Move left, 2: Move right, 3: Move up, 4: Move down
        if self.movement_type == "smooth":
            low = np.array([-1, -1, 0], dtype=np.float32)
            high = np.array([1, 1, 1], dtype=np.float32)
            self.action_space = spaces.Box(low=low, high=high)

        low = np.array([-1, -1, -1, -1], dtype=np.float32)
        high = np.array([1, 1, 1, 1], dtype=np.float32)
        self.observation_space = spaces.Box(low=low, high=high)

        self.aim_trainer_instance = aim_trainer(render_mode=render_mode)

    def reset(self, seed=None, render_mode=None, options=None):
        self.aim_trainer_instance.reset(render_mode=render_mode)

        return np.zeros(4, dtype=np.float32), {}

    def simpleAction(self, action):
        if action == 0:
            self.aim_trainer_instance.handle_input('left arrow')
        elif action == 1:
            self.aim_trainer_instance.handle_input('right arrow')
        elif action == 2:
            self.aim_trainer_instance.handle_input('up arrow')
        elif action == 3:
            self.aim_trainer_instance.handle_input('down arrow')
        elif action == 4:
            self.aim_trainer_instance.handle_input('e')
        self.aim_trainer_instance.step()

    def smoothAction(self, action):
        self.aim_trainer_instance.smooth_input(action)
        self.aim_trainer_instance.step()

    def simpleReward(self, action, angles, beforeDMG):
        beforeXY, beforeZX, thetaXY, thetaZX = angles[0], angles[1], angles[2], angles[3]
        reward = 0
        if action != 4:
            reward = (abs(beforeXY) - abs(thetaXY)) * 4 + (abs(beforeZX) - abs(thetaZX)) * 4
        if beforeDMG != self.aim_trainer_instance.Enemies[0].health:
            reward += 3
        if action == 4 and beforeDMG == self.aim_trainer_instance.Enemies[0].health:
            reward -= 1
        return reward

    def smoothReward(self, action, angles, beforeDMG):
        beforeXY, beforeZX, thetaXY, thetaZX = angles[0], angles[1], angles[2], angles[3]
        reward = (abs(beforeXY) - abs(thetaXY)) * 4 + (abs(beforeZX) - abs(thetaZX)) * 4
        if beforeDMG != self.aim_trainer_instance.Enemies[0].health:
            reward += 3
        if action[2] != 0 and beforeDMG == self.aim_trainer_instance.Enemies[0].health:
            reward -= 1
        return reward

    def step(self, action):
        beforeXY, beforeZX = self.getAngleToEnemy()
        beforeDMG = self.aim_trainer_instance.Enemies[0].health

        if self.movement_type == "simple":
            self.simpleAction(action)
        if self.movement_type == "smooth":
            self.smoothAction(action)

        thetaXY, thetaZX = self.getAngleToEnemy()

        if self.movement_type == "simple":
            reward = self.simpleReward(action, [beforeXY, beforeZX, thetaXY, thetaZX], beforeDMG)
        if self.movement_type == "smooth":
            reward = self.smoothReward(action, [beforeXY, beforeZX, thetaXY, thetaZX], beforeDMG)

        observation = np.array([np.cos(thetaXY), np.sin(thetaXY), np.cos(thetaZX), np.sin(thetaZX)], dtype=np.float32)

        terminated = False
        truncated = False
        info = {}

        return (observation, reward, terminated, truncated, info)

    def getAngleToEnemy(self):
        enemy = self.aim_trainer_instance.Enemies[0].world_position
        pivot = self.aim_trainer_instance.player.camera_pivot 
        offset = enemy - pivot.world_position

        target_yaw = np.arctan2(offset.x, offset.z)
        target_pitch = -np.arctan2(
            offset.y, 
            np.hypot(offset.x, offset.z)
        )

        current_yaw = np.deg2rad(pivot.rotation_y)
        current_pitch = np.deg2rad(pivot.rotation_x)

        yaw_error = (target_yaw - current_yaw + np.pi) % (2 * np.pi) - np.pi
        pitch_error = (target_pitch - current_pitch + np.pi) % (2 * np.pi) - np.pi

        return yaw_error, pitch_error

    def close(self):
        self.aim_trainer_instance.close()