import base64
import io
import imageio
import time
import math
import numpy as np
from torch import Tensor
from PIL import Image
from backend.loader.decorator import KatzukiNode
from backend.nodes.builtin import BaseNode


class DebugSendImageToNeRFPanel(BaseNode):

    @KatzukiNode(hidden=True)
    def __init__(self) -> None:
        pass

    def execute(self, image: Tensor) -> None:
        numpy_image = (image.squeeze().permute(1, 2, 0).cpu().numpy() + 1.0) * 127.5
        pil_image = Image.fromarray(np.uint8(numpy_image))
        image_buffer = io.BytesIO()
        pil_image.save(image_buffer, format='PNG')

        self.set_output("render", f"data:image/png;base64,{base64.b64encode(image_buffer.getvalue()).decode('utf-8')}")
        self.send_update()
        return None


class DebugSendError(BaseNode):

    @KatzukiNode(hidden=True)
    def __init__(self) -> None:
        pass

    def execute(self) -> None:
        self.set_output("error", f"This is a test error message.")
        self.send_update()
        return None


class DebugVideoStreamer(BaseNode):

    @KatzukiNode(hidden=False)
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
            self.set_output("render", f"data:image/png;base64,{base64.b64encode(image_buffer.getvalue()).decode('utf-8')}")
            print(f"Sending frame {step} of {n_frames}")
            self.send_update()

            time.sleep(max(1.0 / fps - (time.time() - start_time), 0))

        return None
