import yaml
import torch

from lerobot.policies.pi05 import PI05Policy
from lerobot.policies.factory import make_pre_post_processors

from fastapi import FastAPI
from utils import Input, Output, select_device

device = select_device()
print(f"Using device: {device}")

# Load configuration
with open('config.yaml', 'r') as f:
    config = yaml.load(f, Loader=yaml.FullLoader)
    repo_id = config['repo_id']
    print(f"Using model from repository: {repo_id}")


# Start server
app = FastAPI()

# Load policy
policy = PI05Policy.from_pretrained(repo_id, device_map=device).eval()

preprocess, postprocess = make_pre_post_processors(
    policy.config,
    repo_id,
    preprocessor_overrides={"device_processor": {"device": str(device)}},
)

@app.post("/predict/", response_class=Output)
def predict(raw_data) -> Output:

    print("Received request with data:", raw_data)
    raw_data = Input.parse_raw(raw_data)
    
    raw_data = {
        "observation.image.head": raw_data.image_head_tensor.permute(2, 0, 1),
        "observation.image.hand": raw_data.image_hand_tensor.permute(2, 0, 1),
        "observation.state": raw_data.observation,
        "task": raw_data.task
    }

    processed_data = preprocess(raw_data)

    return Output(**postprocess(policy(**processed_data)))