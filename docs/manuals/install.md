
# Installation Manual

## Overview

This document describes the steps required to **install the software and its dependencies**
in order to run and extend the project.

The project is an **academic Python software** designed to be extended with additional
features and analyses. For this reason, testing tools are also considered part of the
installation, as they may be useful to final users and developers.

The project is composed of two main components:
- **PyNeVer** (backend library)
- **NeVer2** (frontend and GUI)

---

## Supported Architectures

The installation procedure is architecture-independent and applies to any system
supporting a compatible Python interpreter.

The project has been tested on:
- **Windows 11**
- **Linux (Ubuntu 20.04 / 22.04)**

---

## System Requirements

The following software must be installed on the system:

- **Python ≥ 3.11**
- **pip** (Python package manager)
- **PyQt6**

Verify the Python version:

```bash
python3 --version
````

---

## Recommended Installation Method

It is strongly recommended to install the project inside a **Python virtual environment**
to avoid conflicts with system-wide packages.

Create and activate a virtual environment in Linux:

```bash
python3 -m venv venv
source venv/bin/activate
```

All subsequent installation steps should be performed with the virtual environment activated.

---

## Python Dependencies

The project requires the following Python libraries:

### Core Dependencies

* `numpy`
* `onnx`
* `torch`
* `torchvision`
* `ortools`
* `multipledispatch`

### Testing Dependencies

* `pytest`
* `pytest-qt`
* `onnxruntime`

Although these libraries are mainly used for testing, they are included in the installation
because the project is intended to be **extended and validated by end users**.
Running and extending tests can therefore be considered part of the expected usage.

Install all dependencies using `pip`:

```bash
pip install numpy onnx torch torchvision onnxruntime ortools multipledispatch pytest pytest-qt
```

---

## Integration Between PyNeVer and NeVer2

NeVer2 uses **PyNeer as its computational backend**.
To enable this integration, `PyNeVer` must be made available as a Python package
to the NeVer2 environment.

This is achieved by installing `PyNeVer` in **editable mode**.
Editable installation allows changes to the PyNeVer source code to be immediately
reflected in NeVer2 without requiring reinstallation, which is particularly useful
for development and extension.

From the **PyNeVer directory** (src/main/PyNeVer) , run:

```bash
pip install -e .
```

This operation **integrates** PyNeVer into the active virtual environment,
making it available to NeVer2 as a backend library.

---

## Installation Completion Check (Optional)

To verify that the installation was successful, you can perform a basic import test:

```bash
python -c "import PyNeVer"
```

If no errors are raised, the software is correctly installed.

---
