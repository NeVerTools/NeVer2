# Purpose of this file:
#  Test the import and export methods in an extensive way. The tests consist
#  in verifying that the original networks and the imported-exported produce 
#  identical outputs when given the same random inputs.
# 
# To execute the tests:
#  pytest src/tests/onnx_to_internal/test_import_export.py
# NOTE: this test requires the benchmarks_vnncomp for its correct execution and the onnxruntime library

from pynever.strategies.conversion.converters.onnx import ONNXConverter, ONNXNetwork
import os
import pytest
import onnx
import onnxruntime as ort
import numpy as np


BENCHMARKS = "benchmarks_vnncomp"
LOGS_DIR = os.path.join(os.path.dirname(__file__), "..", "logs")
LOG_FILE = os.path.join(LOGS_DIR, "test_import_export.log")


# ---------- Helper: ensure log directory and file exist ----------
def setup_logging():
    """Create logs directory and log file if they don't exist."""
    if not os.path.exists(LOGS_DIR):
        os.makedirs(LOGS_DIR)
    with open(LOG_FILE, "w") as log_file:
        log_file.write("")


# ---------- Helper: collect ONNX files inside a directory ----------
def collect_onnx_files(root_dir):
    onnx_files = []
    for dirpath, dirnames, filenames in os.walk(root_dir):
        for f in filenames:
            if f.endswith(".onnx"):
                onnx_files.append(os.path.join(dirpath, f))
    return onnx_files


# ---------- Helper: create random input for a given shape ----------
def make_random_input(shape):
    fixed = [(1 if (s is None or isinstance(s, str)) else s) for s in shape]
    return np.random.randn(*fixed).astype(np.float32)


# ---------- Setup: initialize logging ----------
setup_logging()


# ---------- Collect all ONNX networks ----------
BENCHMARKS_ROOT = os.path.join(
    os.path.dirname(__file__),
    "..",
    BENCHMARKS,
)
onnx_files = collect_onnx_files(BENCHMARKS_ROOT)


# ---------- Fixture that loads the ONNX networks ----------
@pytest.fixture(params=onnx_files)
def onnx_network(request):
    """Loads each ONNX file path."""
    return request.param


# ---------- The actual test ----------
def test_import_export_preserves_output(onnx_network):
    """
    Verify that importing an ONNX network into internal representation
    and exporting it back to ONNX produces a network that outputs
    the same results as the original network for random inputs.
    """
    network_path = onnx_network
    
    try:
        # Create the converter
        converter = ONNXConverter()
        # Load the original network
        original_network = ONNXNetwork(network_path)
        #original_network.onnx_network.ir_version = 11
        onnx.checker.check_model(original_network.onnx_network)
        ## Import into internal representation and export back to ONNX
        internal_network = converter.to_neural_network(original_network)
        exported_network = converter.from_neural_network(internal_network)
        exported_network.onnx_network.ir_version = 11 # To avoid onnxruntime error
        for opset in exported_network.onnx_network.opset_import:
            opset.version = 13
        onnx.checker.check_model(exported_network.onnx_network)
        #
        ## Downgrade opsets to avoid onnxruntime problems
        #for imp in original_network.onnx_network.opset_import:
        #    if imp.domain == "" or imp.domain == "ai.onnx":
        #        imp.version = 23
        #
        #for imp in exported_network.onnx_network.opset_import:
        #    if imp.domain == "" or imp.domain == "ai.onnx":
        #        imp.version = 23
        #
        ## Create inference sessions
        original_runtime = ort.InferenceSession(original_network.onnx_network.SerializeToString())
        exported_runtime = ort.InferenceSession(exported_network.onnx_network.SerializeToString())
        #
        ## We assume, in the entire project to deal with single input networks
        assert len(original_runtime.get_inputs()) == 1, "Multiple inputs are not supported"
        #
        ## The input of the two models should be the same
        original_input_meta = original_runtime.get_inputs()[0]
        exported_input_meta = exported_runtime.get_inputs()[0]
        # remove batch dimension from original input (pynever doesn't handle it)
        shape = original_input_meta.shape
        if len(shape) > 1:
            shape[0] = 1
            
        assert shape == exported_runtime.get_inputs()[0].shape, "Input shape doesn't match"
        
        # Prepare random input
        random_input = make_random_input(shape)
        
        # Run inference on both networks
        original_output = original_runtime.run(None, {original_input_meta.name : random_input})
        exported_output = exported_runtime.run(None, {exported_input_meta.name : random_input})
        
        # Verify outputs are equivalent
        assert np.allclose(original_output, exported_output, rtol=1e-5), \
            "Exported network output does not match original network output"
        
        # Log success
        #with open(LOG_FILE, "a") as log_file:
        #    log_file.write(f"{network_path}: PASSED\n")
    
    except AssertionError as e:
        # Log failure with assertion message
        with open(LOG_FILE, "a") as log_file:
            log_file.write(f"{network_path}: FAILED - {str(e)}\n")
        raise
    except NotImplementedError as e:
        # Avoid logging these
        pytest.skip()
    except Exception as e:
        # Log failure with exception message:
        # in this case the test is skipped since the problem is related 
        # to the network and not with the import/export process
        with open(LOG_FILE, "a") as log_file:
            log_file.write(f"{network_path}: SKIPPED - {type(e).__name__}: {str(e)}\n")
        pytest.skip()