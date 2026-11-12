import torch
from torch import nn
import numpy as np
import argparse
import pandas as pd
from pathlib import Path
import pretty_output

class Classifier(nn.Module):
    def __init__(self):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(4, 32),
            nn.ReLU(),
            nn.Linear(32, 16),
            nn.ReLU(),
            nn.Linear(16, 5),
        )

    def forward(self, x):
        return self.net(x)  # Raw class scores (logits)

def train(dataset, saveFolder, epochs, completion=None):
    model = Classifier()
    loss_fn = nn.CrossEntropyLoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=0.001)

    df = pd.read_csv(dataset)
    df_input = df.iloc[:, :4]
    df_output = df.iloc[:, [-1]]
    X = torch.tensor(df_input.values.tolist(), dtype=torch.float32)
    y = torch.tensor(df_output.squeeze().tolist(), dtype=torch.long)

    # Training
    model.train()
    for epoch in range(epochs):
        optimizer.zero_grad()
        logits = model(X)
        loss = loss_fn(logits, y)
        loss.backward()
        optimizer.step()

        if completion is not None:
            completion.value = (epoch + 1) / epochs

    folder = Path(saveFolder)
    folder.mkdir(parents=True, exist_ok=True)

    torch.save(model.state_dict(), folder / "model.pt")

def run(modelFolder, time, movement_type="simple", completion=None):
    from aim_trainer_env import AimTrainerEnv

    folder = Path(modelFolder)
    model = Classifier()
    model.load_state_dict(
        torch.load(folder / "model.pt", weights_only=True)
    )
    model.eval()

    game = AimTrainerEnv(render_mode="playback", movement_type=movement_type)

    obs,_ = game.reset()
    with torch.no_grad():
        for step in range(time):
            np_obs = np.array(obs, dtype=np.float32)
            new_input = torch.as_tensor(np_obs).unsqueeze(0)
            action = model(new_input).argmax(dim=1).item()

            obs, reward, terminated, truncated, info = game.step(action=action)

            if completion is not None:
                completion.value = (step + 1) / time



def main():
    #Add the arguments for the command.
    parser = argparse.ArgumentParser(description="Train a RL model for the Aim Trainer environment.")
    parser.add_argument("mode", type=str, help="What mode to use train / run")
    parser.add_argument("--dataset", type=str, help="Dataset to train on.")
    parser.add_argument("--epochs", type=int, default=100, help="Total number of epochs for training the model.")
    parser.add_argument("--model-path", type=str, default="DLmodels/DLmodel", help="Path to save the trained model. / Path of model to run")
    parser.add_argument("--time", type=int, default=1000, help="The number of timesteps to simulate")

    args = parser.parse_args()

    config_valid = True

    # Validate the arguments
    if args.epochs < 0 or args.epochs > 10_000:
        config_valid = False
        pretty_output.warning("Epochs must be between 1 and 10,000")

    if config_valid:
        if args.mode == "train":
            train(dataset=args.dataset,epochs=args.epochs,saveFolder=args.model_path)
        if args.mode == "run":
            run(modelFolder=args.model_path, time=args.time)

if __name__ == "__main__":
    main()