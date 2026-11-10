import asyncio
from multiprocessing import Process, Value, Queue
from queue import Empty
from pathlib import Path
from collections.abc import Iterable
from textual import on, work
from textual.app import App, ComposeResult
from contextlib import redirect_stdout, redirect_stderr
from textual.widgets import (
    Button,
    Footer,
    Header,
    Input,
    Label,
    Switch,
    ProgressBar,
    Static,
    TabbedContent,
    TabPane,
    DirectoryTree,
    RichLog
)

class FileTree(DirectoryTree):
    def filter_paths(self, paths: Iterable[Path]):
        return [
            path
            for path in paths
            if path.is_dir() or path.suffix.lower() == ".zip"
        ]

class QueueOutput:
    def __init__(self, queue):
        self.queue = queue

    def write(self, text):
        if text:
            self.queue.put(text)
        return len(text)

    def flush(self):
        pass

def playback_with_output(queue, *args):
    import traceback

    output = QueueOutput(queue)

    with redirect_stdout(output), redirect_stderr(output):
        try:
            from model_viewer import view_model
            view_model(*args)
        except Exception:
            traceback.print_exc()
            raise
        finally:
            queue.put(None)

def train_with_output(queue, *args):
    import traceback

    output = QueueOutput(queue)

    with redirect_stdout(output), redirect_stderr(output):
        try:
            from train import Train
            Train(*args)
        except Exception:
            traceback.print_exc()
            raise
        finally:
            queue.put(None)

class SharpshootTUI(App):
    TITLE = "SharpshootAI"
    BINDINGS = [("q", "quit", "Quit")]

    CSS= """
    TabbedContent {
        height: 1fr;
    }

    ListView {
        height: 8;
        border: solid $primary;
    }

    Input, Select {
        margin-bottom: 1;
    }

    .buttons {
        height: 3;
        margin-top: 1;
    }

    Button {
        margin-right: 1;
    }

    #status {
        margin: 1 0;
    }

    RichLog {
        height: 10;
        border: solid $secondary;
    }
    """

    def __init__(self):
        super().__init__()

    def compose(self) -> ComposeResult:
        folder = Path(__file__).resolve().parent / "models"
        yield Header()

        with TabbedContent():
            with TabPane("Train"):
                yield Static("Select training params", id="selection")

                yield Label("Model Name")
                yield Input(value="Model Name", id="model_name")

                yield Label("Smooth movement (off = simple)")
                yield Switch(value=False, id="train_smooth")

                yield Label("Timesteps")
                yield Input(value="100000", type="integer", id="train_timesteps")

                yield Label("Save checkpoints")
                yield Input(value="10000", type="integer", id="train_checkpoints")

                yield Button("Train", id="train")
            with TabPane("View"):
                yield FileTree(folder, id="Files")
                yield Static("Select a ZIP file", id="selected", markup=False)

                yield Label("Smooth movement (off = simple)")
                yield Switch(value=False, id="smooth")

                yield Label("Timesteps")
                yield Input(value="1000", type="integer", id="timesteps")

                yield Button("Run", id="run", variant="success")
            with TabPane("Logs"):
                yield RichLog(id="output", markup=False, wrap=True, max_lines=2000)
                
        yield Static("Idle", id="status")
        yield ProgressBar(total=100, show_eta=False, id="progress")
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "run":
            selected_path = getattr(self, "selected_path", None)
            smooth = self.query_one("#smooth", Switch).value
            movement_type = "smooth" if smooth else "simple"
            timesteps = int(self.query_one("#train_timesteps", Input).value)

            self.query_one("#status", Static).update(
                "Running model_viewer (May take a few moments to appear)"
            )

            self.launch_playback(model_path=selected_path, movement_type=movement_type,
                       timesteps = timesteps)
        if event.button.id == "train":
            model_path = Path("models/" + self.query_one("#model_name", Input).value)
            smooth = self.query_one("#train_smooth", Switch).value
            movement_type = "smooth" if smooth else "simple"
            timesteps = int(self.query_one("#train_timesteps", Input).value)
            checkpoints = int(self.query_one("#train_checkpoints", Input).value)

            self.query_one("#status", Static).update(
                "Running training (May take a few moments for progress to start updating)"
            )

            self.launch_training(model_path, movement_type, checkpoints, timesteps)

            

    @work
    async def launch_training(self, model_path, movement_type, save_checkpoints, timesteps):
        completion = Value("d", 0.0)
        output_queue = Queue()

        progress = self.query_one("#progress", ProgressBar)
        status = self.query_one("#status", Static)
        log = self.query_one("#output", RichLog)
        button = self.query_one("#train", Button)

        progress.update(total=100, progress=0)
        button.disabled = True
        status.update("Starting training...")

        process = Process(
            target=train_with_output,
            args=(output_queue, model_path, movement_type, save_checkpoints, timesteps, completion)
        )

        pending = ""
        started = False

        try:
            process.start()
            started = True

            while True:
                # Check before draining so the final batch is also collected.
                finished = not process.is_alive()
                queue_empty = False

                for _ in range(100):
                    try:
                        text = output_queue.get_nowait()
                    except Empty:
                        queue_empty = True
                        break

                    if text is None:
                        continue

                    pending += text

                    while "\n" in pending:
                        line, pending = pending.split("\n", 1)
                        log.write(line.rstrip("\r"))

                progress.update(progress=completion.value * 100)

                if finished and queue_empty:
                    break

                await asyncio.sleep(0.1)

            process.join()

            if process.exitcode == 0:
                status.update("Training finished")
            else:
                status.update(f"Training failed: exit code {process.exitcode}")

        except asyncio.CancelledError:
            status.update("Training cancelled")
            raise

        except Exception as error:
            status.update("Training failed")
            log.write(str(error))

        finally:
            if pending:
                log.write(pending)

            if started:
                if process.is_alive():
                    process.terminate()

                # Wait without blocking Textual's event loop.
                await asyncio.to_thread(process.join)
                process.close()

            output_queue.close()
            button.disabled = False

    @work
    async def launch_playback(self, model_path, movement_type, timesteps):
        completion = Value("d", 0.0)
        output_queue = Queue()

        progress = self.query_one("#progress", ProgressBar)
        status = self.query_one("#status", Static)
        log = self.query_one("#output", RichLog)
        button = self.query_one("#run", Button)

        progress.update(total=100, progress=0)
        button.disabled = True
        status.update("Starting playback...")

        process = Process(
            target=playback_with_output,
            args=(
                output_queue,
                model_path,
                movement_type,
                timesteps,
                completion,
            ),
        )

        pending = ""
        started = False

        try:
            process.start()
            started = True

            while True:
                # Check before draining so the final batch is also collected.
                finished = not process.is_alive()
                queue_empty = False

                for _ in range(100):
                    try:
                        text = output_queue.get_nowait()
                    except Empty:
                        queue_empty = True
                        break

                    if text is None:
                        continue

                    pending += text

                    while "\n" in pending:
                        line, pending = pending.split("\n", 1)
                        log.write(line.rstrip("\r"))

                progress.update(progress=completion.value * 100)

                if finished and queue_empty:
                    break

                await asyncio.sleep(0.1)

            process.join()

            if process.exitcode == 0:
                status.update("Playback finished")
            else:
                status.update(f"Playback failed: exit code {process.exitcode}")

        except asyncio.CancelledError:
            status.update("Playback cancelled")
            raise

        except Exception as error:
            status.update("Playback failed")
            log.write(str(error))

        finally:
            if pending:
                log.write(pending)

            if started:
                if process.is_alive():
                    process.terminate()

                # Wait without blocking Textual's event loop.
                await asyncio.to_thread(process.join)
                process.close()

            output_queue.close()
            button.disabled = False



    def on_directory_tree_file_selected(self, event: DirectoryTree.FileSelected):
        self.selected_path = event.path

        self.query_one("#selected", Static).update(
            f"Selected: {self.selected_path}"
        )

if __name__ == "__main__":
    SharpshootTUI().run()