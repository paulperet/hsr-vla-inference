from utils import Input, Output
import torch
import requests

import requests
import numpy as np

resp = requests.post("http://localhost:8000/predict", json={
    "image_head_tensor": torch.randn(480, 640, 3).tolist(),
    "image_hand_tensor": torch.randn(480, 640, 3).tolist(),
    "observation": torch.randn(8).tolist(),
    "task": "example_task",
    "previous_actions" : torch.zeros((20, 11), dtype=float).tolist()
})

resp = torch.tensor(resp.json()["action"])
print(resp.shape)
print(resp)