import setuptools

with open('README.md', 'r', encoding='utf-8') as fh:
    long_description = fh.read()

setuptools.setup(
    name='NeVer2',
    version='2.0.3',
    author='Stefano Demarchi',
    author_email='stefano.demarchi@edu.unige.it',
    license='GNU General Public License with Commons Clause License Condition v1.0',
    description='Tool for the creation, conversion, training and verification of Neural Network models.',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/NeVerTools/NeVer2',
    packages=setuptools.find_packages(),
    classifiers=[
        'Programming Language:: Python:: 3.11',
        'Development Status:: 4 - Beta',
        'Topic:: Scientific/Engineering:: Artificial Intelligence',
        'Operating System:: OS Independent',
    ],
    python_requires='>=3.11',
    install_requires=['pynever', 'PyQt6'],
)
