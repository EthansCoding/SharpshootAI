import gymnasium as gym
from stable_baselines3 import PPO
from aim_trainer_env import AimTrainerEnv
from pathlib import Path
import argparse
import pretty_output

#Add the arguments for the command.
parser = argparse.ArgumentParser(description="Train a PPO model for the Aim Trainer environment.")
parser.add_argument("--timesteps", type=int, default=100_000, help="Total number of timesteps for training the model.")
parser.add_argument("--model-path", type=str, default="models/ppo_aim_trainer", help="Path to save the trained model.")
parser.add_argument("--movement-type", type=str, default="simple", help="Type of movement smooth is default")
parser.add_argument("--save-checkpoints", type=int, default=10_000, help="Number of timesteps between saving the model.")

args = parser.parse_args()

config_valid = True

# Validate the arguments
if args.timesteps < 0 or args.timesteps > 4_000_000:
    config_valid = False
    pretty_output.warning("Time steps must be between 1 and 4,000,000")
if args.movement_type not in ["simple", "smooth"]:
    config_valid = False
    pretty_output.warning("movement-type must be either simple or smooth")
if args.save_checkpoints < 1 or args.save_checkpoints > 1_000_000:
    config_valid = False
    pretty_output.warning("save-checkpoints must be between 1 and 1,000,000")

if config_valid:
    models_dir = Path(args.model_path)
    models_dir.mkdir(parents=True, exist_ok=True)

    env = AimTrainerEnv(render_mode=None, movement_type=args.movement_type)

    #initialize the PPO model with MlpPolicy and the AimTrainerEnv environment
    model = PPO("MlpPolicy", env, verbose=1)

    timesteps_per_checkpoint = args.save_checkpoints
    total_timesteps = 0

    #Train the model and save checkpoints at specified intervals
    while total_timesteps < args.timesteps:
        model.learn(
            total_timesteps = timesteps_per_checkpoint,
            progress_bar = True
        )
        total_timesteps += timesteps_per_checkpoint
        model_name = f"model_{total_timesteps // 1000}k"
        model.save(models_dir / model_name)

    env.close()