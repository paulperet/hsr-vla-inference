from pydantic import BaseModel
import torch

# Input data

class Input(BaseModel):
    image_head_tensor: list[list[list[float]]]
    image_hand_tensor: list[list[list[float]]]
    observation: list[float]
    task: str
    previous_actions: list[list[float]]
class Output(BaseModel):
    action: list[list[list[float]]]


# Device selection
def select_device():
    if torch.cuda.is_available():
        return torch.device("cuda")
    elif torch.backends.mps.is_available():
        return torch.device("mps")
    else:    
        return torch.device("cpu")