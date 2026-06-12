from utils import Input, Output
import torch
import requests

input_data = Input(
    image_head_tensor=torch.rand(480, 640, 3),
    image_hand_tensor=torch.rand(480, 640, 3),
    observation=torch.rand(8),
    task="some_task"
).json()

response = requests.post("http://localhost:8000/predict/", json=input_data)
#print(Output.parse_raw(response))