# Tests

This folder contains all the test cases for the extended software project regarding **pyNeVer** and **NeVer2**.

## Directory Overview

The tests are organized by the software module they verify:

### PyNeVer and Never2 Tests

| Module    | Test Name | File | Purpose |
|-----------|-----------|------|---------|
| PyNeVer  | Normalization Test | `onnx_to_internal/test_normalize_fc_layers.py` | Checks the normalization of `Add` + `MatMul` layers into fully connected layers during ONNX-to-internal network conversion. |
| PyNeVer  | is_sequential (ONNX) Test | `onnx_to_internal/test_sequential_onnx.py` | Verifies the correctness of the `is_sequential` function during ONNX-to-internal conversion. |
| PyNeVer  | ONNX Import/Export Test | `onnx_to_internal/test_import_export.py` | Ensures that importing an ONNX network into pynever and then exporting it produces the same network as the original. |
| PyNeVer  | is_sequential (PyTorch) Test | `pytorch_is_sequential/test_sequential_pytorch.py` | Verifies the `is_sequential` function during PyTorch-to-internal conversion. |
| PyNeVer  | PyTorch Import/Export Test | `pytorch_import_export/test_pytorch_import_export.py` | Ensures that importing a PyTorch network into pynever and then exporting it produces the same network as the original. |
| Never2   | Branch Opening Test | `tests_gui/test_gui_branch_opening/test_gui_branch_opening.py` | Checks the correct behavior of opening branches in the GUI. |
| Never2   | Branch Closing Test | `tests_gui/test_gui_add_concat/test_gui_add_concat.py` | Verifies the correct behavior when closing branches. |
| Never2   | Node Removal Test | `tests_gui/test_gui_node_removal/test_gui_node_removal.py` | Ensures nodes are removed correctly in the GUI and internal data structures. |

## Running the Tests

- It is recommended to use a **Python virtual environment**.  
- Run tests using **pytest**.