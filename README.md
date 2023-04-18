# NeVer2

__NeVer2__ is a tool for the learning and verification of neural networks.
See the [LICENSE](https://github.com/NeVerTools/NeVer2/blob/main/LICENSE.txt) 
for usage terms. \
__NeVer2__ is written in Python, and relies on the 
[pyNeVer](https://www.github.com/nevertools/pynever) API.

---
## Execution requirements

__NeVer2__ can be executed on any system running Python >= 3.9.5 \
The instructions below have been tested on Windows, 
Ubuntu Linux and Mac OS x86 and ARM-based Mac OS.

## Linux, Mac OS x86 & Windows
The packages required in order to run __NeVer2__ are the [pyNeVer](https://www.github.com/nevertools/pynever) API
and the [PyQt6](https://www.riverbankcomputing.com/software/pyqt/) framework, which can be installed via PIP

```bash
pip install pynever PyQt6
```

After the installation, you can run __NeVer2__ from the root directory

```bash
python NeVer2/never2.py
```

## ARM-based Mac OS

Since the Python packages needed are incompatible with "Python for ARM Platform" you can install 
[miniforge](https://github.com/conda-forge/miniforge) for arm64 (Apple Silicon) and create a Python virtual environment.

Create a new environment using Python 3.9.5 and activate it

```bash
$ conda create -n myenv python=3.9.5
$ conda activate myenv
$ conda install -c apple tensorflow-deps
```

You can now run PIP for installing the libraries and run __NeVer2__

```bash
$ pip install tensorflow-macos tensorflow-metal
$ pip install pynever PyQt6
$ python NeVer2/never2.py
```

Note that each time you want to run __NeVer2__ you'll need to activate the Conda environment.


## Examples and tutorials

We provide some tutorials for the construction, learning and 
verification of networks thanks to Andrea Gimelli, Karim Pedemonte and 
Giacomo Rosato

* A [Convolutional Network](https://nevertools.github.io/tutorial_fmnist.html)
for the fMNIST dataset
* A [Fully Connected Network](https://nevertools.github.io/tutorial_james.html) 
for a robotics dataset.
