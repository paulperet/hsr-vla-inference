import os

import yaml
import torch

from lerobot.policies.pi05 import PI05Policy, PI05Config
from lerobot.configs.types import RTCAttentionSchedule
from lerobot.policies.rtc.configuration_rtc import RTCConfig
from lerobot.policies.rtc.action_queue import ActionQueue
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

REPO_ID = str(os.environ.get("REPO_ID", "paulprt/pi05-hsr-80k"))
PORT = int(os.environ.get("PORT", 8000))
INFERENCE_DELAY = int(os.environ.get("INFERENCE_DELAY", 4))

# Start server
app = FastAPI()

@serve.deployment()
@serve.ingress(app)
class HSRInferenceServer:
    def __init__(self):

        policy_cfg = PI05Config()

        policy_cfg.rtc_config = RTCConfig(
            enabled=True,
            execution_horizon=10,  # How many steps to blend with previous chunk
            max_guidance_weight=10.0,  # How strongly to enforce consistency
            prefix_attention_schedule=RTCAttentionSchedule.EXP,  # Exponential blend
        )

        self.policy = torch.compile(PI05Policy.from_pretrained(REPO_ID, policy_cfg=policy_cfg, device=device)).eval()
        self.preprocess, self.postprocess = make_pre_post_processors(
            self.policy.config,
            REPO_ID,
            preprocessor_overrides={"device_processor": {"device": str(device)}},
        )

        # Now use predict_action_chunk with RTC parameters
        self.inference_delay = INFERENCE_DELAY  # How many steps of inference latency, this values should be calculated based on the inference latency of the policy

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
        
        previous_actions = torch.tensor(raw_data.previous_actions)

        # Useful data debug
        # print(data["observation.image.hand"].shape)
        # print(data["observation.image.head"].shape)
        # print(data["observation.state"].shape)
        # print(data["task"])
        
        data = self.preprocess(data)

        # Predict the action chunk
        with torch.inference_mode():
            action_chunk = self.policy.predict_action_chunk(data, inference_delay=self.inference_delay, prev_chunk_left_over=previous_actions)

        action_chunk = self.postprocess(action_chunk)

        response = Output(action=action_chunk.cpu().tolist())

        return response
    
serve.start(http_options={"host": "0.0.0.0", "port": PORT})
serve.run(HSRInferenceServer.bind(), route_prefix="/")
time.sleep(60*60*24) # Keep the server running for 1 day