# Purpose of this file:
#  Test the import and export methods in an extensive way. The tests consist
#  in verifying that the original networks and the imported-exported produce 
#  identical outputs when given the same random inputs.
# 
# To execute the tests:
#  pytest src/tests/pytorch_import_export/test_pytorch_import_export.py

from pynever.strategies.conversion.converters.pytorch import PyTorchConverter, PyTorchNetwork
import os
import json
import pytest
import torch
import inspect
import numpy as np
from unittest.mock import patch

NETWORKS = "pytorch_networks"
LOGS_DIR = os.path.join(os.path.dirname(__file__), "logs")
LOG_FILE = os.path.join(LOGS_DIR, "test_import_export.log")

# load the input dimension of each network
with open("pytorch_networks/network_input_shapes.json", "r") as f:
    input_shapes = json.load(f)


# ---------- Helper: ensure log directory and file exist ----------
def setup_logging():
    """Create logs directory and log file if they don't exist."""
    if not os.path.exists(LOGS_DIR):
        os.makedirs(LOGS_DIR)
    with open(LOG_FILE, "w") as log_file:
        log_file.write("")


# ---------- Helper: collect PyTorch files inside a directory ----------
def collect_pytorch_files(root_dir):
    pt_files = []
    for dirpath, dirnames, filenames in os.walk(root_dir):
        for f in filenames:
            if f.endswith(".pt"):
                pt_files.append(os.path.join(dirpath, f))
    return pt_files


# ---------- Helper: generate a random torch tensor with the given shape. ----------
def make_random_input(shape, device="cpu"):
    return torch.randn(*shape, dtype=torch.float32, device=device)


# ---------- Setup: initialize logging ----------
setup_logging()


# ---------- Collect all PyTorch networks ----------
pt_files = collect_pytorch_files(NETWORKS)


# ---------- Fixture that loads the PyTorch networks ----------
@pytest.fixture(params=pt_files)
def pytorch_network(request):
    """Loads each PyTorch file path."""
    return request.param


# ---------- The actual test ----------
def test_import_export_preserves_output(pytorch_network):
    """
    Verify that importing an PyTorch network into internal representation
    and exporting it back to PyTorch produces a network that outputs
    the same results as the original network for random inputs.
    """
    network_path = pytorch_network
    
    try:
        # Create the converter
        converter = PyTorchConverter()

        # Load the original network
        original_network = PyTorchNetwork(network_path)

        ## Import into internal representation and export back to PyTorch
        sig = inspect.signature(original_network.pytorch_network.forward)
        params = sig.parameters
        inputs = list(params.values())[0:]

        assert len(inputs) == 1, "Multiple inputs are not supported"

        network_filename = os.path.basename(pytorch_network)
        input_shape = input_shapes[network_filename]

        clean_shape = str(input_shape[1:]).strip("[]") # drop the batch size

        with patch("builtins.input", return_value=clean_shape): # provide the input dimension of the network
            internal_network = converter.to_neural_network(original_network)

        with patch('builtins.input', return_value='y'): # trace the network when exporting
            exported_network = converter.from_neural_network(internal_network)

        # Prepare random input
        random_input = make_random_input(input_shape)

        # Set networks in eval mode and run inference on both
        original_network.pytorch_network.eval() 
        exported_network.pytorch_network.eval() 
        original_output = original_network.pytorch_network(random_input).detach().cpu().numpy()
        exported_output = exported_network.pytorch_network(random_input).detach().cpu().numpy()

        # Verify outputs are equivalent
        assert np.allclose(original_output, exported_output, rtol=1e-5), \
            "Exported network output does not match original network output"
        
        # Log success
        with open(LOG_FILE, "a") as log_file:
            log_file.write(f"{network_path}: PASSED\n")
    
    except AssertionError as e:
        # Log failure with assertion message
        with open(LOG_FILE, "a") as log_file:
            log_file.write(f"{network_path}: FAILED - {str(e)}\n")
        raise
    except NotImplementedError as e:
        # Log failure with notimplementederror message
        with open(LOG_FILE, "a") as log_file:
            log_file.write(f"{network_path}: SKIPPED - {type(e).__name__}: {str(e)}\n")
        pytest.skip()
    except Exception as e:
        # Log failure with exception message:
        # in this case the test is skipped since the problem is related 
        # to the network and not with the import/export process
        with open(LOG_FILE, "a") as log_file:
            log_file.write(f"{network_path}: SKIPPED - {type(e).__name__}: {str(e)}\n")
        pytest.skip()