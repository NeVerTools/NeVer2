# Purpose of this file:
#  test the ONNXConverter.__is_sequential_onnx method against a set of networks divided in
#  sequential and non-sequential networks.
# 
# To execute the tests:
#  pytest src/tests/onnx_to_internal/test_sequential_onnx.py
# NOTE: this test requires the benchmarks_vnncomp for its correct execution

from pynever.strategies.conversion.converters.onnx import ONNXConverter, ONNXNetwork
import os
import pytest

BENCHMARKS = "benchmarks_vnncomp"
FULLYCONNECTED_BENCHMARKS = "fullyconnected_benchmarks_vnncomp"
RESIDUAL_BENCHMARKS = "residual_benchmarks_vnncomp"
# ---------- Helper: collect ONNX files inside a directory ----------
def collect_onnx_files(root_dir):
    onnx_files = []
    for dirpath, dirnames, filenames in os.walk(root_dir):
        for f in filenames:
            if f.endswith(".onnx"):
                onnx_files.append(os.path.join(dirpath, f))
    return onnx_files


# ---------- Collect networks expected to be sequential ----------
SEQUENTIAL_ROOT = os.path.join(
    os.path.dirname(__file__),
    "..",
    BENCHMARKS,
    FULLYCONNECTED_BENCHMARKS
)
sequential_onnx_files = collect_onnx_files(SEQUENTIAL_ROOT)


# ---------- Collect networks expected to be non-sequential (residual) ----------
NONSEQ_ROOT = os.path.join(
    os.path.dirname(__file__),
    "..",
    BENCHMARKS,
    RESIDUAL_BENCHMARKS
)
nonsequential_onnx_files = collect_onnx_files(NONSEQ_ROOT)


# ---------- Fixtures that load the ONNX networks ----------
@pytest.fixture(params=sequential_onnx_files)
def sequential_network(request):
    """Loads each sequential network ONNX file as an ONNXNetwork."""
    return ONNXNetwork(request.param)


@pytest.fixture(params=nonsequential_onnx_files)
def nonsequential_network(request):
    """Loads each non-sequential (residual) ONNX file as an ONNXNetwork."""
    return ONNXNetwork(request.param)


# ---------- The actual tests ----------
def test_sequential_networks_are_detected(sequential_network):
    """All fully connected benchmarks should be sequential."""
    assert ONNXConverter._ONNXConverter__is_sequential_onnx(sequential_network)


def test_nonsequential_networks_are_detected(nonsequential_network):
    """All residual benchmarks should NOT be sequential."""
    assert not ONNXConverter._ONNXConverter__is_sequential_onnx(nonsequential_network)
