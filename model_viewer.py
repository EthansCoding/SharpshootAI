from stable_baselines3 import PPO
from aim_trainer_env import AimTrainerEnv

model = PPO.load("models/ppo_aim_trainer.zip", env=AimTrainerEnv(render_mode="human"))

obs = model.env.reset()

for _step in range(1000):
    action, _ = model.predict(
        obs,
        deterministic=True
    )
    print(f"Obs: {obs}")
    obs, reward, terminated, truncated = model.env.step(action)