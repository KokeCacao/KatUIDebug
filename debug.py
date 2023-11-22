import base64
import numpy as np
from torch import Tensor
from PIL import Image
from io import BytesIO
from backend.loader.decorator import KatachiNode
from backend.nodes.builtin import BaseNode


class DebugSendImageToNeRFPanel(BaseNode):

    @KatachiNode(hidden=True)
    def __init__(self) -> None:
        pass

    def execute(self, image: Tensor) -> None:
        numpy_image = (image.squeeze().permute(1, 2, 0).cpu().numpy() + 1.0) * 127.5
        pil_image = Image.fromarray(np.uint8(numpy_image))
        image_buffer = BytesIO()
        pil_image.save(image_buffer, format='PNG')
        image_bytes = image_buffer.getvalue()

        self.set_output("render", f"data:image/png;base64,{base64.b64encode(image_bytes).decode('utf-8')}")
        self.send_update()
        return None


class DebugSendError(BaseNode):

    @KatachiNode(hidden=True)
    def __init__(self) -> None:
        pass

    def execute(self) -> None:
        self.set_output("error", f"This is a test error message.")
        self.send_update()
        return None
