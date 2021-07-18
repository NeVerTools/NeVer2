import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="NeVer2",
    version="0.1.1.dev2",
    author="Dario Guidotti, Stefano Demarchi",
    author_email="{dario.guidotti|stefano.demarchi}@edu.unige.it",
    license='GNU General Public License with Commons Clause License Condition v1.0',
    description="Tool for the creation and the conversion of Neural Network models.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/NeVerTools/NeVer2",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language:: Python:: 3.8",
        "Development Status:: 3 - Alpha",
        "Topic:: Scientific/Engineering:: Artificial Intelligence",
        "Operating System:: OS Independent",
    ],
    python_requires='>=3.8',
    install_requires=['numpy', 'PyQt5', 'pynever', 'onnx', 'torch', 'tensorflow', 'pysmt'],
)

