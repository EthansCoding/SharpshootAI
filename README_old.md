MVP:
Create an ML model that can automatically aim at enemy targets.
The model will control a player that can only look L/R and U/D at constant rates.
It will be fed in the angle from its current looking direction to the goal direction.
Using that to move the camera to focus on the target. It will be rewarded for movement towards
the goal. Rewarded heavily for being on top of and aiming at the goal.

Tech Stack -- Python only:
Python with Ursina for the game logic.
Gymnassium for the ML environment.
Stable Baselines 3 for training and model development.

1. Setup file structure project, git init, uv init, requirements.txt and readme.md
2. Setup aim_trainer.py. It should be a template 3d level.
3. Setup aim_trainer.py to be an aim trainer esque game. No movement, shoot spheres floating.
4. Build aim_trainer_env.py which is a gymnassium env that can run the game logic with / without rendering the game.
5. Add reward function to aim_trainer_env.py.
6.Create a train.py that uses SB3 with the gym and train for a suitable number of steps.
7. Create a model_runner.py file that runs the model specified by params and lets you watch a model play the aim trainer.
8. (Optional) Create a leaderboard of the models created so far. Create up to 5 models trained differently. Present which one turned out the best
