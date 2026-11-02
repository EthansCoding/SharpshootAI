from stable_baselines3 import PPO
from aim_trainer_env import AimTrainerEnv
from pathlib import Path
import pretty_output
import argparse

parser = argparse.ArgumentParser(description="Playback a specific model that has been trained to play AimTrainer")

parser.add_argument("model", type=str,help="Path to the model folder")
parser.add_argument("--time", type=int, default=1000, help="The number of steps to simulate")
parser.add_argument("--movement-type", type=str, default="simple", help="The type of model!")

args = parser.parse_args()

config_valid = True

modelPath = Path(args.model+"/model.zip")

if args.time < 1 or args.time > 1_000_000:
    config_valid = False
    pretty_output.warning(f"--time: {args.time} is out of bounds 1 to 1,000,000")
if not modelPath.exists():
    config_valid = False
    pretty_output.warning(f"{modelPath} does not exist, check if the model is stored at that location")
if args.movement_type not in ["simple", "smooth"]:
    config_valid = False
    pretty_output.warning(f"{args.movement_type} is not a valid choice. Choose either simple or smooth, and make sure it correlates with the trained model")
else:
    try:
        model = PPO.load(modelPath, env=AimTrainerEnv(render_mode="playback", movement_type=args.movement_type))
    except:
        config_valid = False
        correct_type = "smooth"
        if args.movement_type == "smooth": print = "simple"
        pretty_output.warning(f"Wrong movement-type for this model, use {correct_type} instead.")

if config_valid:
    obs = model.env.reset()

    for _step in range(args.time):
        action, _ = model.predict(
            obs,
            deterministic=True
        )
        
        obs, reward, terminated, truncated = model.env.step(action)