import gymnasium as gym
from stable_baselines3 import PPO
from aim_trainer_env import AimTrainerEnv
from pathlib import Path

models_dir = Path(__file__).parent / "models"
models_dir.mkdir(parents=True, exist_ok=True)

env = AimTrainerEnv(render_mode=None)

model = PPO("MlpPolicy", env, verbose=1)

model.learn(total_timesteps = 100000)
model.save(models_dir / "ppo_aim_trainer")

env.close()