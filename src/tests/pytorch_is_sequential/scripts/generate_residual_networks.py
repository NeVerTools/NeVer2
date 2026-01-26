import torch
import os
import torch.nn as nn
import torch.fx as fx

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
RESIDUAL_DIR   = os.path.join(ROOT_DIR, "residual_networks")
os.makedirs(RESIDUAL_DIR, exist_ok=True)

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
        self.conv = nn.Conv2d(3, 6, 3)
        self.pool = nn.MaxPool2d(2)
        self.conv2 = nn.Conv2d(6, 6, 3)
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
        self.conv1 = nn.Conv1d(4, 8, 3)
        self.conv2 = nn.Conv1d(8, 8, 3)
        self.conv3 = nn.Conv1d(8, 8, 3)
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
        self.conv1 = nn.Conv2d(1, 2, 3)
        self.pool = nn.AvgPool2d(2)
        self.conv2 = nn.Conv2d(2, 2, 3)
        
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
]

for i, (model, example_input) in enumerate(networks, 1):
    traced = fx.symbolic_trace(model)
    filename = f"residual_net{i}_traced.pt"
    torch.save(traced, os.path.join(RESIDUAL_DIR, filename))
    print(f"Saved: {filename}")
