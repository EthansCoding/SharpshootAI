import gymnasium as gym
from stable_baselines3 import PPO
from aim_trainer_env import AimTrainerEnv
from pathlib import Path
import argparse
import pretty_output

parser = argparse.ArgumentParser(description="Train a PPO model for the Aim Trainer environment.")
parser.add_argument("--timesteps", type=int, default=100_000, help="Total number of timesteps for training the model.")
parser.add_argument("--model-path", type=str, default="models/ppo_aim_trainer", help="Path to save the trained model.")
parser.add_argument("--movement-type", type=str, default="simple", help="Type of movement smooth is default")

args = parser.parse_args()

config_valid = True

if args.timesteps < 0 or args.timesteps > 4_000_000:
    config_valid = False
    pretty_output.warning("Time steps must be between 1 and 4,000,000")
if args.movement_type not in ["simple", "smooth"]:
    config_valid = False
    pretty_output.warning("movement-type must be either simple or smooth")

if config_valid:
    models_dir = Path(args.model_path)
    models_dir.mkdir(parents=True, exist_ok=True)

    env = AimTrainerEnv(render_mode=None, movement_type=args.movement_type)

    model = PPO("MlpPolicy", env, verbose=1)

    model.learn(
        total_timesteps = args.timesteps,
        progress_bar = True
    )
    model.save(models_dir / "model")

    env.close()