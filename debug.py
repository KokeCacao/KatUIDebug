import base64
import io
import imageio
import time
import math
import numpy as np
import urllib.request
import urllib.error

from typing import Any, Dict, Tuple, TypedDict, List
from torch import Tensor
from PIL import Image
from backend.loader.decorator import KatzukiNode
from backend.nodes.builtin import BaseNode


class DebugInfiniteLoop(BaseNode):
    """This node is to test "pause", "resume", "stop" functions that is already implemented in all nodes.
    This node will also introduce you to the annotation `@KatzukiNode()`.
    Note that this description will be interpreted by `@KatzukiNode()` and
    show in the UI as node description only if "node_description" is not specified.
    """

    class ReturnDict(TypedDict):
        output_name: float # this name will be shown in to output connection
        another_output: str # this name will be shown in to output connection

    @KatzukiNode(
        # node_type: You can customize the internal ID of the node,
        #            If you don't specify this, the internal ID will be
        #            generated as "debug.debug_infinite_loop" because
        #            it will include the file name and class name in snake case.
        #            You can find this node in "Debug/InfiniteLoop" on [Tab] UI.
        node_type="debug.infinite_loop",
        # hidden: If you set this to True, this node will be hidden in the UI.
        #         And you can't find it in [Tab] UI.
        hidden=False,
        # singleton: If true, only one instance of this node can be created in a graph.
        singleton=False,
        # persistent: If true, this node cannot be deleted by user.
        persistent=False,
        # inoperable: If true, this node cannot be run (there won't be a button).
        signal_to_default_data={
            # There will be a "break" and a "clear" button in UI
            # once you click them, the node will receive a signal containing message
            "break": "hey! stop looping and give me a value~",
            "turn": "please change direction",
        },
        author="ProudlyPut YourNameHere",
        author_link="https://proundly.put.your.website.here",
        node_description="Oh well, I override the docstring above.",
        input_description={
            "snake_case_variable": "This is a description for snake_case_variable",
            "and_they_must_be_fully_typed": "This is a description for and_they_must_be_fully_typed",
        },
        output_description={
            "output_name": "This is a description for output_name",
            "another_output": "This is a description for another_output",
        },
    )
    def __init__(self) -> None:
        pass

    def execute(
            self,
            snake_case_variable: int,
            # defaults are fine, but don't put heavy computation on defaults.
            # as they will be evaluated at the time of backend initialization.
            and_they_must_be_fully_typed: float = 114.514,
            # Avoid using numbers in your variables.
            # This is because we need to ensure one to one mapping
            # between `calmelCase` and `snake_case`,
            # but both `variable_num_1` and `variable_num1` maps
            # to `variableNum1`, losing information.
            *args_are_fine: Tuple[Any, ...], # it must be typed as Tuple[???, ...]
            **kwargs_are_fine_as_well: Dict[str, Any], # it must be typed as Dict[str, ???]
    ) -> ReturnDict:
        # get some nice gif image for us to animate
        def get_gif(url: str = "https://upload.wikimedia.org/wikipedia/commons/0/07/The_Horse_in_Motion-anim.gif"):
            frames: List[str] = []

            try:
                req = urllib.request.Request(url, data=None, headers={'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36'})
                # if fetch from web success, convert frames to a list of base64 encoded image
                img = Image.open(urllib.request.urlopen(req))
                i = 0
                while True:
                    frame = img.copy()
                    image_buffer = io.BytesIO()
                    frame.save(image_buffer, format="PNG")
                    frames.append(f"data:image/png;base64,{base64.b64encode(image_buffer.getvalue()).decode('utf-8')}")
                    i += 1
                    try:
                        img.seek(img.tell() + 1)
                    except EOFError:
                        break
            except urllib.error.HTTPError as e:
                # this will make the progress bar to red and send an error message
                # indicate there is an error executing this node.
                self.set_output("error", f"Failed to get gif from {url}")
                self.send_update()
                raise Exception(f"Failed to get gif from {url}")
            return frames

        forward = True
        progress = 0
        frames = get_gif()
        while True:
            # this will check if user clicked "stop" (to kill node) or "pause" button
            # and it will check if user clicked any user defined signal above
            # if so, signal will be set to corresponding text.
            # please put this function in your loop, otherwise you can't stop your loop.
            signal = self.check_execution_state_change(clear_signal_event=lambda signal: signal == "hey! stop looping and give me a value~" # since we handled "hey! stop looping and give me a value~" signal
                                                       or signal == "please change direction" # since we handled "please change direction" signal
                                                       or True # since we handled everything else
                                                      )
            if signal is None:
                # that means user didn't click any custom button
                pass
            elif signal == "hey! stop looping and give me a value~":
                break
            elif signal == "please change direction":
                forward = not forward
            else:
                self.set_output("error", f"Unknown signal {signal}")
                self.send_update()
                raise Exception(f"Unknown signal {signal}")

            if forward:
                progress = (progress + 1) % len(frames)
            else:
                progress = (progress - 1) % len(frames)

            # this will be shown to progress bar. "progress" is a special keyword
            self.set_output(key="progress", value=progress / len(frames) * 100)
            # this will be shown to NeRF panel. "render" is a special keyword
            # render only accept base64 encoded string for now
            # TODO: let it accept tensor image, or even numpy image
            self.set_output(
                key="render",
                value={
                    # image below is the background of NeRF Panel of UI
                    "image": frames[progress],
                    # the below is to show "virtual camera" in NeRF Panel of UI
                    # c2w is camera to world matrix, specifying camera transform
                    # image is the image stick on the camera
                    # focal is the focal length of the camera
                    # "dataset": [
                    #     {
                    #         "c2w": nerf_dataset.c2w,
                    #         "image": nerf_dataset.image,
                    #         "focal": nerf_dataset.focal,
                    #     },
                    #     ...
                    # ]
                    # You can get current view parameter of NeRF Panel with
                    # variable.ip2render[variable.sid2ip[self._sid]]
                    # You can see a concrete example in KatUIDiffusionBasics/nerf.py
                })
            # this will be shown to "output" of the node.
            # it accepts pytorch tensor or base64 encoded string.
            # if value is a tensor image of shape [B, C, H, W], [C, H, W], [H, W, C], or [B, H, W, C]
            # and in range [-1, 1], [0, 1], or [0, 255], it will be shown as image.
            # if batch size B > 1, it will be shown as animated gif.
            self.set_output(key="Eadweard Muybridge's Galloping Horse", value=frames[progress])

            self.send_update() # the above update will not send to frontend until you call this function
            time.sleep(1)

        # You can also detect which output is required by the user
        # This can save same GPU memory when user don't need to load specific models
        output_name_is_connected = "output_name" in self._connected_outputs

        # If you want your output to be named, write a "ReturnDict" like above
        # and return a filled dict like below.
        return self.ReturnDict(
            output_name=snake_case_variable,
            another_output=f"I'm another output, and we looped {progress} times. And {'output_name is connected' if output_name_is_connected else 'output_name is not connected'}",
        )
        # If you have only single output, then you can do the following:
        # but please wrap it in "ReturnDict" if your single output is a Dict
        # return snake_case_variable


class DebugSendImageToNeRFPanel(BaseNode):

    @KatzukiNode()
    def __init__(self) -> None:
        pass

    def execute(self, image: Tensor) -> None:
        numpy_image = (image.squeeze().permute(1, 2, 0).cpu().numpy() + 1.0) * 127.5
        pil_image = Image.fromarray(np.uint8(numpy_image))
        image_buffer = io.BytesIO()
        pil_image.save(image_buffer, format='PNG')

        self.set_output("render", {"image": f"data:image/png;base64,{base64.b64encode(image_buffer.getvalue()).decode('utf-8')}"})
        self.send_update()
        return None


class DebugCustomHttpRequest(BaseNode):

    @KatzukiNode(inoperable=True)
    def __init__(self) -> None:
        pass

    def execute(self) -> None:
        return None


class DebugCrash(BaseNode):

    @KatzukiNode()
    def __init__(self) -> None:
        pass

    def execute(self) -> None:
        raise Exception("This is a test exception.")


class DebugSendError(BaseNode):

    @KatzukiNode()
    def __init__(self) -> None:
        pass

    def execute(self) -> None:
        self.set_output("error", f"This is a test error message.")
        self.send_update()
        return None


class DebugDevice(BaseNode):

    @KatzukiNode()
    def __init__(self) -> None:
        pass

    def execute(self, tensor: Any) -> str:
        return str(tensor.device)


class DebugDir(BaseNode):

    @KatzukiNode()
    def __init__(self) -> None:
        pass

    def execute(self, obj: Any) -> str:
        return str(dir(obj))


class DebugAccessField(BaseNode):

    @KatzukiNode()
    def __init__(self) -> None:
        pass

    def execute(self, obj: Any, field: str) -> Any:
        return getattr(obj, field)


class DebugVideoStreamer(BaseNode):

    @KatzukiNode()
    def __init__(self) -> None:
        pass

    def execute(self, video_path: str) -> None:
        reader = imageio.get_reader(video_path)
        meta_data = reader.get_meta_data()
        fps = meta_data.get('fps', 30)
        n_frames = meta_data.get('nframes', float('inf')) # Get the number of frames
        print(f"Found {n_frames} frames in video {video_path}")

        for step, frame in enumerate(reader.iter_data()):
            start_time = time.time()
            pil_img = Image.fromarray(frame)
            image_buffer = io.BytesIO()
            pil_img.save(image_buffer, format="PNG")

            self.set_output("progress", int(100 * math.ceil(step / n_frames)))
            self.set_output("render", {"image": f"data:image/png;base64,{base64.b64encode(image_buffer.getvalue()).decode('utf-8')}"})
            print(f"Sending frame {step} of {n_frames}")
            self.send_update()

            time.sleep(max(1.0 / fps - (time.time() - start_time), 0))

        return None


class ExampleWithContext(BaseNode):

    @KatzukiNode()
    def __init__(self) -> None:
        pass

    class WithContext:

        def __init__(self):
            self.value = 42

        def __enter__(self):
            print("Entering with statement")
            return self

        def __exit__(self, exc_type, exc_value, traceback) -> None:
            print("Exiting with statement")
            return None

    def execute(self) -> WithContext:
        return self.WithContext()


class Print(BaseNode):

    @KatzukiNode()
    def __init__(self) -> None:
        pass

    def execute(self, input: Any) -> str:
        print(input)
        return str(input)
