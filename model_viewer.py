from stable_baselines3 import PPO
from aim_trainer_env import AimTrainerEnv
from pathlib import Path
import pretty_output
import argparse

def main():
    #This adds the arguments
    parser = argparse.ArgumentParser(description="Playback a specific model that has been trained to play AimTrainer")
    parser.add_argument("model", type=str,help="Path to the model folder")
    parser.add_argument("--time", type=int, default=1000, help="The number of steps to simulate")
    parser.add_argument("--movement-type", type=str, default="simple", help="The type of model!")

    args = parser.parse_args()

    config_valid = True

    '''
    This validates the model and what model is being ran.
    '''
    folder = Path(args.model)
    if not folder.is_dir():
        config_valid = False
        pretty_output.warning(f"{folder} is not a valid directory")

    files = sorted(folder.glob("*.zip"))
    if len(files) == 0:
        config_valid = False
        pretty_output.warning(f"No model files found in {folder}")
    for number, path in enumerate(files, start=1):
        print(f"{number}: {path.name}")

    while True:
        try:
            choice = int(input("Select a model to playback by entering the corresponding number: "))
            if 1 <= choice <= len(files):
                modelPath = files[choice - 1]
                break
            else:
                print(f"Invalid choice. Please enter a number between 1 and {len(files)}.")
        except ValueError:
            print("Invalid input. Please enter a valid number.")
            pass

    if args.time < 1 or args.time > 1_000_000:
        config_valid = False
        pretty_output.warning(f"--time: {args.time} is out of bounds 1 to 1,000,000")
    if args.movement_type not in ["simple", "smooth"]:
        config_valid = False
        pretty_output.warning(f"{args.movement_type} is not a valid choice. Choose either simple or smooth, and make sure it correlates with the trained model")
    if config_valid:
        view_model(modelPath, args.movement_type, args.time)

def view_model(modelPath, movement_type, time, completion=None):
    if completion is not None:
        completion.value = 0.0
    config_valid = True
    try:
        model = PPO.load(modelPath, env=AimTrainerEnv(render_mode="playback", movement_type=movement_type))
    except:
        config_valid = False
        correct_type = "smooth"
        if movement_type == "smooth": correct_type = "simple"
        pretty_output.warning(f"Wrong movement-type for this model, use {correct_type} instead.")

    if config_valid:
        obs = model.env.reset()

        count = 0
        '''
        Step through for all of the time steps and play it back for the user.
        '''
        for _step in range(time):
            action, _ = model.predict(
                obs,
                deterministic=True
            )

            count += 1
            if completion is not None:
                completion.value = count / time

            obs, reward, terminated, truncated = model.env.step(action)
        model.env.close()

if __name__ == "__main__":
    main()