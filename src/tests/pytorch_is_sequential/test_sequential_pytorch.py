# Purpose of this file:
#  test the PyTorchConverter._PyTorchConverter__is_sequential_pytorch method against a set of networks divided in
#  sequential and non-sequential networks.
# 
# To execute the tests:
#  pytest src/tests/pytorch_to_internal/test_sequential_pytorch.py

from pynever.strategies.conversion.converters.pytorch import PyTorchConverter
from pynever.strategies.conversion.representation import PyTorchNetwork
import os
import pytest

SEQUENTIAL_NETWORKS_DIR = "sequential_networks"
RESIDUAL_NETWORKS_DIR = "residual_networks"

# ---------- Helper: collect PyTorch files inside a directory ----------
def collect_pytorch_files(root_dir):
    pytorch_files = []
    for dirpath, dirnames, filenames in os.walk(root_dir):
        for f in filenames:
            if f.endswith(".pt"):
                pytorch_files.append(os.path.join(dirpath, f))
    return pytorch_files

# ---------- Collect traced networks expected to be sequential ----------
SEQUENTIAL_ROOT = os.path.join(
    os.path.dirname(__file__),
    SEQUENTIAL_NETWORKS_DIR
)
sequential_PyTorch_files = collect_pytorch_files(SEQUENTIAL_ROOT)

# ---------- Collect traced networks expected to be non-sequential (residual) ----------
NONSEQ_ROOT = os.path.join(
    os.path.dirname(__file__),
    RESIDUAL_NETWORKS_DIR
)
nonsequential_PyTorch_files = collect_pytorch_files(NONSEQ_ROOT)

# ---------- Fixtures that load the PyTorch networks ----------
@pytest.fixture(params=sequential_PyTorch_files)
def sequential_network(request):
    """Loads each sequential network PyTorch file as an PyTorchNetwork."""
    return PyTorchNetwork(request.param)

@pytest.fixture(params=nonsequential_PyTorch_files)
def nonsequential_network(request):
    """Loads each non-sequential (residual) PyTorch file as an PyTorchNetwork."""
    return PyTorchNetwork(request.param)

# ---------- The actual tests ----------
def test_sequential_networks_are_detected(sequential_network):
    """All sequential networks should be sequential."""
    assert PyTorchConverter._PyTorchConverter__is_sequential_pytorch(sequential_network)

def test_nonsequential_networks_are_detected(nonsequential_network):
    """All residual networks should NOT be sequential."""
    assert not PyTorchConverter._PyTorchConverter__is_sequential_pytorch(nonsequential_network)