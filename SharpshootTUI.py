import asyncio
from multiprocessing import Process, Value, Queue, Array
from queue import Empty
from pathlib import Path
from collections.abc import Iterable
from textual import on, work
from textual.app import App, ComposeResult
from textual.containers import Horizontal
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

'''
Textual class item that draws a directory with all paths and .zip files.
'''
class FileTree(DirectoryTree):
    def filter_paths(self, paths: Iterable[Path]):
        return [
            path
            for path in paths
            if path.is_dir() or path.suffix.lower() == ".zip"
        ]

'''
QueueOutput creates a queue of the logs from the programs we run from this TUI
'''
class QueueOutput:
    def __init__(self, queue):
        self.queue = queue

    def write(self, text):
        if text:
            self.queue.put(text)
        return len(text)

    def flush(self):
        pass

'''
This runs the model viewer without output in the TUI, and instead sent to a queue.
'''
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

'''
This runs the training without output in the TUI, instead sent to a richlog.
'''
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

'''
This is the TUI app
'''
class SharpshootTUI(App):
    TITLE = "SharpshootAI"
    BINDINGS = [("q", "quit", "Quit")]
    DEFAULT_THEME = "rose-pine-moon"

    CSS= """
    TabbedContent {
        height: 1fr;
    }

    ListView {
        height: 8;
        border: solid $primary;
    }

    Input, Select, Switch {
        margin-bottom: 1;
    }

    .buttons {
        height: 3;
        margin-top: 1;
    }

    Button {
        align: center top;
        margin-right: 1;
    }

    #status {
        width: 100%;
        text-align: center;
        margin: 1 0;
    }

    #progress {
        width: 100%;
    }

    #progress Bar {
        width: 1fr;
    }

    RichLog {
        height: 1fr;
        border: solid $secondary;
    }

    .button-row {
        width: 100%;
        height: auto;
        align-horizontal: center;
    }

    #selected {
        width: 100%;
        text-align: center;
    }
    """

    def __init__(self):
        super().__init__()

    '''
    This function composes the panes of the app, add to it to have more items
    in the app
    '''
    def compose(self) -> ComposeResult:
        folder = Path(__file__).resolve().parent / "models"
        yield Header()

        with TabbedContent():
            with TabPane("Train"):
                yield Label("Model Name")
                yield Input(value="Model Name", id="model_name")

                yield Label("Smooth movement (off = simple)")
                yield Switch(value=False, id="train_smooth")

                yield Label("Timesteps")
                yield Input(value="100000", type="integer", id="train_timesteps")

                yield Label("Save checkpoints")
                yield Input(value="10000", type="integer", id="train_checkpoints")

                with Horizontal(classes="button-row"):
                    yield Button("Train", id="train", variant="success")
            with TabPane("View", id="view-pane"):
                yield FileTree(folder, id="Files")
                yield Static("Select a ZIP file", id="selected", markup=False)

                yield Label("Smooth movement (off = simple)")
                yield Switch(value=False, id="smooth")

                yield Label("Timesteps")
                yield Input(value="1000", type="integer", id="timesteps")

                with Horizontal(classes="button-row"):
                    yield Button("Run", id="run", variant="success")
            with TabPane("Logs"):
                yield RichLog(id="output", markup=False, wrap=True, max_lines=2000)
            with TabPane("Training-Data"):
                yield Static("Kills: 0", id="kills")
                yield Static("Avg Kill Time: 0.00s", id="killtimes")
                
        yield Static("Idle", id="status")
        yield ProgressBar(total=100, show_eta=False, id="progress")
        yield Footer()

    #Runs on button press, currently hooked into train and run buttons.
    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "run":
            selected_path = getattr(self, "selected_path", None)
            smooth = self.query_one("#smooth", Switch).value
            movement_type = "smooth" if smooth else "simple"
            timesteps = int(self.query_one("#timesteps", Input).value)

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

    '''
    This function launches the training asynchronously
    '''
    @work
    async def launch_training(self, model_path, movement_type, save_checkpoints, timesteps):
        #These variables are all information we are getting back from the other program.
        completion = Value("d", 0.0)
        output_queue = Queue()
        data = Array("d", [0.0, 0.0])

        #These are the buttons, statics, progress bar and rich log.
        progress = self.query_one("#progress", ProgressBar)
        status = self.query_one("#status", Static)
        log = self.query_one("#output", RichLog)
        button = self.query_one("#train", Button)
        kills = self.query_one("#kills", Static)
        killtimes = self.query_one('#killtimes', Static)

        #Set some start values
        progress.update(total=100, progress=0)
        button.disabled = True
        status.update("Starting training...")

        #Create a train with output process.
        process = Process(
            target=train_with_output,
            args=(output_queue, model_path, movement_type, save_checkpoints, timesteps, completion, data)
        )

        pending = ""
        started = False

        try:
            #Start the process
            process.start()
            started = True

            while True:
                # Check before draining so the final batch is also collected.
                finished = not process.is_alive()
                queue_empty = False

                #This clears 100 outputs of the queue.
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

                #Update progress, kills and killtimes.
                progress.update(progress=completion.value * 100)
                kills.update(f"Kills: {int(data[0])}")
                killtimes.update(f"Avg Kill Time: {data[1]: .2f}")

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
            #Write any extra text
            if pending:
                log.write(pending)

            if started:
                #Cancel if hasn't been quit yet.
                if process.is_alive():
                    process.terminate()

                # Wait without blocking Textual's event loop.
                await asyncio.to_thread(process.join)
                process.close()

            #Re-enable button, close queue
            output_queue.close()
            button.disabled = False

    '''
    Very very similar function to the above launch_training, see comments from that.
    '''
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
                completion
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

    '''
    When you open the view pane, it runs this which reloads our file explorer.
    '''
    @on(TabbedContent.TabActivated, pane="#view-pane")
    def refresh_model_files(self):
        self.query_one("#Files", DirectoryTree).reload()

    '''
    When a file is selected it sets the path variable and updates text
    '''
    def on_directory_tree_file_selected(self, event: DirectoryTree.FileSelected):
        self.selected_path = event.path

        self.query_one("#selected", Static).update(
            f"Selected: {self.selected_path}"
        )

    '''
    When opened it changes the theme to rose-pine-moon as the default theme 
    '''
    def on_mount(self):
        self.theme = self.DEFAULT_THEME

if __name__ == "__main__":
    SharpshootTUI().run()