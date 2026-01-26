import torch
import os
import torch.nn as nn
import torch.fx as fx

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SEQUENTIAL_DIR = os.path.join(ROOT_DIR, "sequential_networks")
os.makedirs(SEQUENTIAL_DIR, exist_ok=True)

class Net1(nn.Module):
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

class Net2(nn.Module):
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

class Net3(nn.Module):
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

class Net4(nn.Module):
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

class Net5(nn.Module):
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

class Net6(nn.Module):
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

class Net7(nn.Module):
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

class Net8(nn.Module):
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

class Net9(nn.Module):
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

class Net10(nn.Module):
    def __init__(self):
        super().__init__()
        self.fc1 = nn.Linear(10, 5)
        self.celu = nn.CELU()
        self.fc2 = nn.Linear(5, 5)

    def forward(self, x):
        x = self.fc1(x)
        x = self.celu(x)
        x = torch.cat([x], dim=1) 
        x = self.fc2(x)
        return x

networks = [
    (Net1(),  torch.randn(1, 1, 28, 28)),
    (Net2(),  torch.randn(1, 3, 32, 32)),
    (Net3(),  torch.randn(1, 4, 100)),
    (Net4(),  torch.randn(1, 1, 10, 10, 10)),
    (Net5(),  torch.randn(1, 100)),
    (Net6(),  torch.randn(1, 3, 32, 32)),
    (Net7(),  torch.randn(1, 1, 28, 28)),
    (Net8(),  torch.randn(1, 20)),
    (Net9(),  torch.randn(1, 3, 32, 32)),
    (Net10(), torch.randn(1, 10)),
]

for i, (model, example_input) in enumerate(networks, 1):
    traced = fx.symbolic_trace(model)
    filename = f"sequential_net{i}_traced.pt"
    torch.save(traced, os.path.join(SEQUENTIAL_DIR, filename))
    print(f"Saved: {filename}")