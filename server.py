import argparse
from pathlib import Path
import torch

from lerobot.policies.pi05 import Pi05Policy
from lerobot.policies.factory import make_pre_post_processors

from docarray.typing import TorchTensor, NdArray
from docarray import BaseDoc

# Device selection
if torch.cuda.is_available():
    device = torch.device("cuda")
elif torch.backends.mps.is_available():
    device = torch.device("mps")
else:    
    device = torch.device("cpu")

# Input data
class Input(BaseDoc):
    # specify shapes of tensors
    image_head_tensor: TorchTensor[480, 640, 3]
    image_hand_tensor: TorchTensor[480, 640, 3]
    observation: TorchTensor[8]

# Output data
class Output(BaseDoc):
    action: TorchTensor[11]

def main(repo_id: str):

    policy = Pi05Policy.from_pretrained(repo_id, device_map=device).eval()

    preprocess, postprocess = make_pre_post_processors(
        policy.config,
        repo_id,
        preprocessor_overrides={"device_processor": {"device": str(device)}},
    )

def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--repo-id",
        type=str,
        default="lerobot/pi05",
        help="The repository ID of the model to serve.",
    )
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_args()
    main(args.repo_id)