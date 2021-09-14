# NeVer 2

NeVer 2 is a tool for learning and verification of neural networks. 
See the [LICENSE](https://github.com/NeVerTools/NeVer2/blob/main/LICENSE.txt) 
for usage terms. \
Never 2 is written in Python, and relies on the 
[pyNeVer](https://www.github.com/nevertools/pynever) API.

---

# DISCLAIMER: This is an early alpha version, many bugs are yet to be fixed.

---
## Execution requirements

NeVer 2 can be executed on any system running Python >= 3.8. \
The instructions below have been tested on Windows, 
Ubuntu Linux and Mac OS x86 and ARM-based Mac OS.

* ### Linux, Mac OS x86 & Windows
There is a number of Python packages required in order to
run NeVer 2. All the following packages can be installed
via PIP

```bash
pip install numpy PyQt5 onnx torch torchvision pysmt pynever
```

After the installation, you can run NeVer 2 from the root directory

```bash
python NeVer2/never2.py
```

* ### ARM-based Mac OS

Since the Python packages needed are incompatible with "Python for ARM
Platform" you can install [Anaconda](https://www.anaconda.com/) using
Rosetta and create a x86 Python virtual environment.

Create a new environment using Python 3.9.5 and activate it

```bash
$ conda create -n myenv python=3.9.5
$ conda activate myenv
```

You can now run PIP for installing the libraries and run NeVer 2

```bash
$ pip install numpy PyQt5 onnx torch torchvision pysmt pynever
$ python NeVer2/never2.py
```

Note that each time you want to run NeVer 2 you'll need to activate 
the Conda environment.

## Examples and tutorials

We provide some tutorials for the construction, learning and 
verification of networks thanks to Karim Pedemonte, Giacomo Rosato
and Andrea Gimelli.

* A [Convolutional Network](https://nevertools.github.io/tutorial_fmnist.html)
for the fMNIST dataset
* A [Fully Connected Network](https://nevertools.github.io/tutorial_fmnist.html) 
for a robotics dataset.
