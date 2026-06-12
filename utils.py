from docarray.typing import TorchTensor, NdArray
from docarray import BaseDoc

import torch

# Input data
class Input(BaseDoc):
    # specify shapes of tensors
    image_head_tensor: TorchTensor[480, 640, 3]
    image_hand_tensor: TorchTensor[480, 640, 3]
    observation: TorchTensor[8]
    task: str

# Output data
class Output(BaseDoc):
    action: TorchTensor[11]


# Device selection
def select_device():
    if torch.cuda.is_available():
        return torch.device("cuda")
    elif torch.backends.mps.is_available():
        return torch.device("mps")
    else:    
        return torch.device("cpu")