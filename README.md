# NeVer2

__NeVer2__ is a tool for the learning and verification of neural networks.
See the [LICENSE](https://github.com/NeVerTools/NeVer2/blob/main/LICENSE.txt) 
for usage terms. \
__NeVer2__ is written in Python, and relies on the 
[pyNeVer](https://www.github.com/nevertools/pynever) API.

## Publications

Here we collect the bibtex entries on our publications related to __NeVer2__

```
@inproceedings{demarchi2022formal,
    title = {Formal Verification of Neural Networks: a Case Study about Adaptive Cruise Control},
	author = {Demarchi, Stefano and Guidotti, Dario and Pitto, Andrea and Tacchella, Armando},
	year = 2022,
	booktitle = {International ECMS Conference on Modeling and Simulation},
	pages={310--316}
}
```

---
# Setup and execution

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

## Usage

__NeVer2__ is conceived as a GUI where the process of building, training and verifying a
neural network can be managed in a single environment, but it also provides a CLI usage 
for verifying [VNN-LIB](www.vnnlib.org) properties on ONNX models without resorting to the
full-fledged interface.
Typing

```bash
python NeVer2/never2.py -verify <property>.smt2 <network>.onnx [complete | approximate | mixed1 | mixed2]
```

executes the verification procedure for the property specified in the SMT file on the network
specified in the ONNX file. The verification strategy is one among the following:

* _complete_: uses the exact algorithm (for small-sized networks)
* _approximate_: uses the over-approximate algorithm
* _mixed1_: uses the mixed algorithm refining 1 neuron per layer
* _mixed2_: uses the mixed algorithm refining 2 neurons per layer

Details on the algorithms can be found in [our Best Paper @ECMS 2022](https://www.scs-europe.net/dlib/2022/ecms2022acceptedpapers/0310_dis_ecms2022_0075.pdf)

---
# Examples and tutorials

We provide some tutorials for the construction, learning and 
verification of networks thanks to Andrea Gimelli, Karim Pedemonte and 
Giacomo Rosato

* A [Convolutional Network](https://nevertools.github.io/tutorial_fmnist.html)
for the fMNIST dataset
* A [Fully Connected Network](https://nevertools.github.io/tutorial_james.html) 
for a robotics dataset.
