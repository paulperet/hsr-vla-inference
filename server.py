import os

import yaml
import torch

from lerobot.policies.pi05 import PI05Policy
from lerobot.policies.factory import make_pre_post_processors

from fastapi import Body, FastAPI
from utils import Input, Output, select_device
import time
import torch
from ray import serve

device = select_device()


def debug(raw_data):
    from PIL import Image
    import numpy as np
    
    im = Image.fromarray(np.array(raw_data.image_head_tensor, dtype=np.uint8))
    im.save("head.jpeg")

    im = Image.fromarray(np.array(raw_data.image_hand_tensor, dtype=np.uint8))
    im.save("hand.jpeg")

# Disable TorchDynamo and TorchCompile if not using CUDA
# Avoid crash on mps/cpu
if device.type != "cuda":
    os.environ["TORCHDYNAMO_DISABLE"] = "1"
    os.environ["TORCH_COMPILE_DISABLE"] = "1"

print(f"Using device: {device}")

REPO_ID = os.environ.get("REPO_ID", "paulprt/pi05-hsr-80k")

# Start server
app = FastAPI()

@serve.deployment()
@serve.ingress(app)
class HSRInferenceServer:
    def __init__(self):
        self.policy = torch.compile(PI05Policy.from_pretrained(REPO_ID, device_map=device)).eval()
        self.preprocess, self.postprocess = make_pre_post_processors(
            self.policy.config,
            REPO_ID,
            preprocessor_overrides={"device_processor": {"device": str(device)}},
        )

    @app.post("/predict", response_model=Output)
    def predict(self, raw_data:  Input = Body(...)) -> Output:
        # Process the single request.

        #debug(raw_data)

        data = {
            "observation.image.head": torch.tensor(raw_data.image_head_tensor).permute(2, 0, 1).float() / 255.0,
            "observation.image.hand": torch.tensor(raw_data.image_hand_tensor).permute(2, 0, 1).float() / 255.0,
            "observation.state": torch.tensor(raw_data.observation).float(),
            "task": raw_data.task
            }

        # Useful data debug
        # print(data["observation.image.hand"].shape)
        # print(data["observation.image.head"].shape)
        # print(data["observation.state"].shape)
        # print(data["task"])
        
        data = self.preprocess(data)

        # Predict the action chunk
        with torch.inference_mode():
            action_chunk = self.policy.predict_action_chunk(data)

        action_chunk = self.postprocess(action_chunk)

        response = Output(action=action_chunk.cpu().tolist())

        return response
    
serve.start(http_options={"host": "0.0.0.0", "port": 8000})
serve.run(HSRInferenceServer.bind(), route_prefix="/")
time.sleep(60*60*24) # Keep the server running for 1 day