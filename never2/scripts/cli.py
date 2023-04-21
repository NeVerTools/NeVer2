"""
Module cli.py

This module contains command-line interfaces for the verification of
neural networks properties in the VNN-LIB standard
(www.vnnlib.org/#standard)

Author: Stefano Demarchi

"""

import logging
import os
import sys

from pynever.networks import SequentialNetwork
from pynever.strategies import conversion
from pynever.strategies.conversion import ONNXNetwork, ONNXConverter
from pynever.strategies.smt_reading import SmtPropertyParser
from pynever.strategies.verification import NeVerProperty, NeverVerification


def show_help():
    print("usage: python never2.py ... [-verify] [property] [model] [strategy]")
    print()
    print("Options and arguments:")
    print("no args        : launch NeVer2 in GUI mode.")
    print("-verify args   : verify the VNN-LIB property in args[1] on the\n"
          "                 ONNX model in args[2] with the strategy in args[3]")
    print()
    print("[strategy]     : one between 'complete', 'approximate', 'mixed1' or 'mixed2'.")
    print("args ...       : arguments passed to program in sys.argv[1:]")
    print()


def verify_model(property_file: str, model_file: str, strategy: str) -> bool:
    """
    This method starts the verification procedure on the network model
    provided in the model_file path and prints the result

    Parameters
    ----------
    property_file : str
        Path to the .vnnlib or .smt2 file of the property
    model_file : str
        Path to the .onnx file of the network
    strategy : str
        Verification strategy (either complete, approximate, mixed1 or mixed2)

    Returns
    ----------
    bool
        True if the property is verified, False otherwise

    """

    nn_path = os.path.abspath(model_file)
    prop_path = os.path.abspath(property_file)

    if not os.path.isfile(nn_path):
        print('Invalid path for the network model.')
        return False
    elif not os.path.isfile(prop_path):
        print('Invalid path for the property.')
        return False
    else:
        # Read the network file
        alt_repr = conversion.load_network_path(nn_path)

        if alt_repr is not None:
            if isinstance(alt_repr, ONNXNetwork):
                network = ONNXConverter().to_neural_network(alt_repr)

                if isinstance(network, SequentialNetwork):
                    # Read the property file
                    parser = SmtPropertyParser(prop_path, network.input_id,
                                               network.get_last_node().identifier)
                    to_verify = NeVerProperty(*parser.parse_property())

                    # Log to stdout
                    logger = logging.getLogger('pynever.strategies.verification')
                    logger.setLevel(logging.INFO)
                    logger.addHandler(logging.StreamHandler(sys.stdout))

                    ver_strategy = None
                    if strategy == 'complete':
                        ver_strategy = NeverVerification('best_n_neurons',
                                                         [[10000] for _ in range(network.count_relu_layers())])
                    elif strategy == 'approximate':
                        ver_strategy = NeverVerification('best_n_neurons',
                                                         [[0] for _ in range(network.count_relu_layers())])
                    elif strategy == 'mixed1':
                        ver_strategy = NeverVerification('best_n_neurons',
                                                         [[1] for _ in range(network.count_relu_layers())])
                    elif strategy == 'mixed2':
                        ver_strategy = NeverVerification('best_n_neurons',
                                                         [[2] for _ in range(network.count_relu_layers())])

                    return ver_strategy.verify(network, to_verify)
            else:
                print('The model is not an ONNX model.')
                return False
