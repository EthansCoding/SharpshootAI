import gymnasium as gym
from gymnasium import spaces
import numpy as np
from aim_trainer import aim_trainer

'''
Wraps the aim_trainer class into a Gymnasium environment for reinforcement learning.
This class allows the aim_trainer game to be used as an environment for training reinforcement learning models
'''
class AimTrainerEnv(gym.Env):
    '''
    The init for the AimTrainerEnv class. It initializes the environment with the specified render mode and movement type.
    render_mode: str - The mode of the game. It can be "human", "playback" or None. If it is None, the game will be created in logic only mode.
    movement_type: str - The type of movement for the agent. It can be "simple" or "smooth". "simple" uses discrete actions, while "smooth" uses continuous actions.
    '''
    def __init__(self, render_mode=None, movement_type="simple", data=[0, 0]):
        super().__init__()
        self.data = data
        self.movement_type = movement_type
        if self.movement_type == "simple":
            self.action_space = spaces.Discrete(5)  # 0: No action, 1: Move left, 2: Move right, 3: Move up, 4: Move down
        if self.movement_type == "smooth":
            low = np.array([-1, -1, 0], dtype=np.float32)
            high = np.array([1, 1, 1], dtype=np.float32)
            self.action_space = spaces.Box(low=low, high=high)

        low = np.array([-1, -1, -1, -1], dtype=np.float32)
        high = np.array([1, 1, 1, 1], dtype=np.float32)
        self.observation_space = spaces.Box(low=low, high=high)

        self.aim_trainer_instance = aim_trainer(render_mode=render_mode)

    '''
    Reset the environment to its initial state. This method is called at the beginning of each episode.
    '''
    def reset(self, seed=None, options=None):
        self.aim_trainer_instance.reset()

        return np.zeros(4, dtype=np.float32), {}
    
    '''
    Execute a simple action in the environment.
    '''
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

    '''
    Execute a smooth action in the environment.
    The action is a continuous vector where the first two elements represent the movement in the x and
    y directions, and the third element represents whether to shoot or not.'''
    def smoothAction(self, action):
        self.aim_trainer_instance.smooth_input(action)
        self.aim_trainer_instance.step()

    '''
    Calculate the reward for a simple action based on the change in angle to the enemy and whether the enemy was hit.
    '''
    def simpleReward(self, action, angles, beforeDMG):
        beforeXY, beforeZX, thetaXY, thetaZX = angles[0], angles[1], angles[2], angles[3]
        reward = 0
        if action != 4:
            reward = (abs(beforeXY) - abs(thetaXY)) * 4 + (abs(beforeZX) - abs(thetaZX)) * 4
        if beforeDMG != self.aim_trainer_instance.Enemies[0].health:
            reward += 3
        if action == 4 and beforeDMG == self.aim_trainer_instance.Enemies[0].health:
            reward -= 2
        return reward

    '''
    Calculate the reward for a smooth action based on the change in angle to the enemy and whether the enemy was hit.
    '''
    def smoothReward(self, action, angles, beforeDMG):
        beforeXY, beforeZX, thetaXY, thetaZX = angles[0], angles[1], angles[2], angles[3]
        reward = (abs(beforeXY) - abs(thetaXY)) * 4 + (abs(beforeZX) - abs(thetaZX)) * 4
        if beforeDMG != self.aim_trainer_instance.Enemies[0].health:
            reward += 3
        if action[2] >= 0 and beforeDMG == self.aim_trainer_instance.Enemies[0].health:
            reward -= 2
        return reward

    '''
    Take a step in the environment with the given action.
    This method executes the action, calculates the reward, and returns the new observation, reward, termination status, truncation status, and additional info.
    '''
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

        if len(self.aim_trainer_instance.killTimes) > 1:
            durations = [
                (self.aim_trainer_instance.killTimes[i] - self.aim_trainer_instance.killTimes[i - 1]).total_seconds()
                for i in range(1, len(self.aim_trainer_instance.killTimes))
            ]
            average = sum(durations) / len(durations) if durations else 0
        else: average = 0
        self.data[0], self.data[1] = self.aim_trainer_instance.killCount, average

        observation = np.array([np.cos(thetaXY), np.sin(thetaXY), np.cos(thetaZX), np.sin(thetaZX)], dtype=np.float32)

        terminated = False
        truncated = False
        info = {}

        return (observation, reward, terminated, truncated, info)

    '''
    Returns the angle to the enemy in both the XY and ZX planes. This method calculates the yaw and pitch errors based on the current camera orientation and the position of the enemy.
    '''
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

    '''
    Closes the environment and the underlying aim_trainer instance. This method is called when the environment is no longer needed.'''
    def close(self):
        self.aim_trainer_instance.close()