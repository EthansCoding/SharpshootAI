from stable_baselines3 import PPO
from aim_trainer_env import AimTrainerEnv
import argparse

parser = argparse.ArgumentParser(description="Playback a specific model that has been trained to play AimTrainer")

parser.add_argument("model", type=str,help="Path to the model folder")
parser.add_argument("--time", type=int, default=1000, help="The number of steps to simulate")

args = parser.parse_args()

modelPath = args.model+"/model.zip"

model = PPO.load(modelPath, env=AimTrainerEnv(render_mode="playback"))

obs = model.env.reset()

for _step in range(args.time):
    action, _ = model.predict(
        obs,
        deterministic=True
    )

    obs, reward, terminated, truncated = model.env.step(action)