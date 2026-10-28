import gymnasium as gym
from stable_baselines3 import PPO
from aim_trainer_env import AimTrainerEnv
from pathlib import Path
import argparse

parser = argparse.ArgumentParser(description="Train a PPO model for the Aim Trainer environment.")
parser.add_argument("--timesteps", type=int, default=100_000, help="Total number of timesteps for training the model.")
parser.add_argument("--model-path", type=str, default="models/ppo_aim_trainer", help="Path to save the trained model.")

args = parser.parse_args()

models_dir = Path(args.model_path)
models_dir.mkdir(parents=True, exist_ok=True)

env = AimTrainerEnv(render_mode=None)

model = PPO("MlpPolicy", env, verbose=1)

model.learn(
    total_timesteps = args.timesteps,
    progress_bar = True
)
model.save(models_dir / "model")

env.close()