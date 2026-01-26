import torch
import os
import json
import torch.nn as nn
import torch.fx as fx

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
NETWORKS_DIR   = os.path.join(ROOT_DIR, "pytorch_networks")
os.makedirs(NETWORKS_DIR, exist_ok=True)

class Net1(nn.Module):
    def __init__(self):
        super().__init__()
        self.fc1 = nn.Linear(10, 10)
        self.fc2 = nn.Linear(10, 10)
        self.fc3 = nn.Linear(10, 5)
        self.relu = nn.ReLU()
        
    def forward(self, x):
        a = self.fc1(x)
        b = self.fc2(x)
        c = a + b
        c = self.relu(c)
        out = self.fc3(c)
        return out

class Net2(nn.Module):
    def __init__(self):
        super().__init__()
        self.fc1 = nn.Linear(8, 4)
        self.fc2 = nn.Linear(8, 4)
        self.fc3 = nn.Linear(8, 2)
        self.relu = nn.ReLU()

    def forward(self, x):
        a = self.fc1(x)
        b = self.fc2(x)
        c = torch.cat([a, b], dim=1)
        c = self.relu(c)
        out = self.fc3(c)
        return out

class Net3(nn.Module):
    def __init__(self):
        super().__init__()
        self.conv = nn.Conv2d(3, 6, 3, padding=1)
        self.pool = nn.MaxPool2d(2)
        self.conv2 = nn.Conv2d(6, 6, 3, padding=1)
        self.bn = nn.BatchNorm2d(6)
        
    def forward(self, x):
        a = self.conv(x)
        b = self.pool(a)
        c = self.conv2(b)
        out = self.bn(c + b)
        return out

class Net4(nn.Module):
    def __init__(self):
        super().__init__()
        self.conv1 = nn.Conv1d(4, 8, 3, padding=1)
        self.conv2 = nn.Conv1d(8, 8, 3, padding=1)
        self.conv3 = nn.Conv1d(8, 8, 3, padding=1)
        self.relu = nn.ReLU()

    def forward(self, x):
        a = self.conv1(x)
        b = self.conv2(a)
        c = self.conv3(b)
        d = self.relu(a + b + c)
        return d

class Net5(nn.Module):
    def __init__(self):
        super().__init__()
        self.conv1 = nn.Conv3d(1, 4, 3)
        self.conv2 = nn.Conv3d(1, 4, 3)
        self.bn = nn.BatchNorm3d(8)
        self.relu = nn.ReLU()

    def forward(self, x):
        a = self.conv1(x)
        b = self.conv2(x)
        c = torch.cat([a, b], dim=1)
        out = self.relu(self.bn(c))
        return out

class Net6(nn.Module):
    def __init__(self):
        super().__init__()
        self.fc1 = nn.Linear(12, 12)
        self.fc2 = nn.Linear(12, 6)
        self.fc3 = nn.Linear(12, 6)
        
    def forward(self, x):
        a = self.fc1(x)
        b = torch.unsqueeze(a, dim=1)
        c = self.fc2(a)
        d = self.fc3(b.squeeze(1))
        out = c + d
        return out

class Net7(nn.Module):
    def __init__(self):
        super().__init__()
        self.conv = nn.Conv2d(3, 3, 3, padding=1)
        self.bn = nn.BatchNorm2d(3)
        self.relu = nn.ReLU()

    def forward(self, x):
        a = self.conv(x)
        b = self.bn(a)
        c = self.relu(a + b)
        return c

class Net8(nn.Module):
    def __init__(self):
        super().__init__()
        self.fc1 = nn.Linear(6, 3)
        self.fc2 = nn.Linear(6, 3)
        self.fc3 = nn.Linear(6, 2)
        
    def forward(self, x):
        a = self.fc1(x)
        b = self.fc2(x)
        c = torch.cat([a, b], dim=1)
        out = self.fc3(c)
        return out

class Net9(nn.Module):
    def __init__(self):
        super().__init__()
        self.conv1 = nn.Conv2d(1, 2, 3, padding=1)
        self.pool = nn.AvgPool2d(1, stride=1) 
        self.conv2 = nn.Conv2d(2, 2, 3, padding=1)

    def forward(self, x):
        a = self.conv1(x)
        b = self.pool(a)
        c = self.conv2(a + b)
        return c

class Net10(nn.Module):
    def __init__(self):
        super().__init__()
        self.fc1 = nn.Linear(5, 5)
        self.fc2 = nn.Linear(5, 5)
        self.relu = nn.ReLU()
        
    def forward(self, x):
        a = self.fc1(x)
        b = torch.unsqueeze(a, dim=1).squeeze(1)
        c = self.fc2(b)
        out = self.relu(a + c)
        return out
    
class Net11(nn.Module):
    def __init__(self):
        super().__init__()
        self.flatten = nn.Flatten()
        self.fc1 = nn.Linear(28*28, 128)
        self.relu = nn.ReLU()
        self.fc2 = nn.Linear(128, 10)

    def forward(self, x):
        x = self.flatten(x)
        x = self.fc1(x)
        x = self.relu(x)
        x = self.fc2(x)
        return x

class Net12(nn.Module):
    def __init__(self):
        super().__init__()
        self.conv = nn.Conv2d(3, 16, 3, padding=1)
        self.bn = nn.BatchNorm2d(16)
        self.relu = nn.ReLU()
        self.pool = nn.MaxPool2d(2)

    def forward(self, x):
        x = self.conv(x)
        x = self.bn(x)
        x = self.relu(x)
        x = self.pool(x)
        return x

class Net13(nn.Module):
    def __init__(self):
        super().__init__()
        self.conv = nn.Conv1d(4, 8, 5)
        self.pool = nn.AvgPool1d(2)
        self.flatten = nn.Flatten()
        self.fc = nn.Linear(8 * 48, 10)

    def forward(self, x):
        x = self.conv(x)
        x = self.pool(x)
        x = self.flatten(x)
        x = self.fc(x)
        return x

class Net14(nn.Module):
    def __init__(self):
        super().__init__()
        self.conv = nn.Conv3d(1, 4, 3)
        self.bn = nn.BatchNorm3d(4)
        self.elu = nn.ELU()

    def forward(self, x):
        x = self.conv(x)
        x = self.bn(x)
        x = self.elu(x)
        return x

class Net15(nn.Module):
    def __init__(self):
        super().__init__()
        self.fc1 = nn.Linear(100, 50)
        self.tanh = nn.Tanh()
        self.drop = nn.Dropout(0.2)
        self.fc2 = nn.Linear(50, 20)

    def forward(self, x):
        x = self.fc1(x)
        x = self.tanh(x)
        x = self.drop(x)
        x = self.fc2(x)
        return x

class Net16(nn.Module):
    def __init__(self):
        super().__init__()
        self.conv = nn.Conv2d(3, 6, 5)
        self.lrn = nn.LocalResponseNorm(2)
        self.leaky = nn.LeakyReLU()

    def forward(self, x):
        x = self.conv(x)
        x = self.lrn(x)
        x = self.leaky(x)
        return x

class Net17(nn.Module):
    def __init__(self):
        super().__init__()
        self.conv = nn.Conv2d(1, 4, 3)
        self.pool = nn.MaxPool2d(2)
        self.flatten = nn.Flatten()
        self.fc = nn.Linear(4 * 13 * 13, 10)
        self.softmax = nn.Softmax(dim=1)

    def forward(self, x):
        x = self.conv(x)
        x = self.pool(x)
        x = self.flatten(x)
        x = self.fc(x)
        x = self.softmax(x)
        return x

class Net18(nn.Module):
    def __init__(self):
        super().__init__()
        self.fc1 = nn.Linear(20, 20)
        self.relu = nn.ReLU()
        self.fc2 = nn.Linear(20, 10)

    def forward(self, x):
        x = self.fc1(x)
        x = self.relu(x)
        x = self.fc2(x)
        return x

class Net19(nn.Module):
    def __init__(self):
        super().__init__()
        self.conv = nn.Conv2d(3, 8, 3)
        self.flatten = nn.Flatten()
        self.fc = nn.Linear(8 * 30 * 30, 100)

    def forward(self, x):
        x = self.conv(x)
        x = torch.unsqueeze(x, 1)     
        x = self.flatten(x)
        x = self.fc(x)
        return x

class Net20(nn.Module):
    def __init__(self):
        super().__init__()
        self.fc1 = nn.Linear(10, 5)
        self.celu = nn.CELU()
        self.fc2 = nn.Linear(5, 5)

    def forward(self, x):
        x = self.fc1(x)
        x = self.celu(x)
        x = self.fc2(x)
        return x

networks = [
    (Net1(),  torch.randn(1, 10)),
    (Net2(),  torch.randn(1, 8)),
    (Net3(),  torch.randn(1, 3, 32, 32)),
    (Net4(),  torch.randn(1, 4, 20)),
    (Net5(),  torch.randn(1, 1, 10, 10, 10)),
    (Net6(),  torch.randn(1, 12)),
    (Net7(),  torch.randn(1, 3, 32, 32)),
    (Net8(),  torch.randn(1, 6)),
    (Net9(),  torch.randn(1, 1, 16, 16)),
    (Net10(), torch.randn(1, 5)),
    (Net11(),  torch.randn(1, 1, 28, 28)),
    (Net12(),  torch.randn(1, 3, 32, 32)),
    (Net13(),  torch.randn(1, 4, 100)),
    (Net14(),  torch.randn(1, 1, 10, 10, 10)),
    (Net15(),  torch.randn(1, 100)),
    (Net16(),  torch.randn(1, 3, 32, 32)),
    (Net17(),  torch.randn(1, 1, 28, 28)),
    (Net18(),  torch.randn(1, 20)),
    (Net19(),  torch.randn(1, 3, 32, 32)),
    (Net20(), torch.randn(1, 10)),
]

# Dictionary to store filename -> input shape
input_shapes_dict = {}

for i, (model, example_input) in enumerate(networks, 1):
    # Trace model (optional, you can save state_dict instead)
    traced = fx.symbolic_trace(model)
    
    # Filename for saving
    filename = f"net{i}_traced.pt"
    filepath = os.path.join(NETWORKS_DIR, filename)
    
    # Save traced model
    torch.save(traced, filepath)
    print(f"Saved: {filename}")
    
    # Store input shape
    input_shapes_dict[filename] = list(example_input.shape)

# Save input shapes to JSON
json_path = os.path.join(NETWORKS_DIR, "network_input_shapes.json")
with open(json_path, "w") as f:
    json.dump(input_shapes_dict, f, indent=4)

print(f"Saved input shapes JSON: {json_path}")

