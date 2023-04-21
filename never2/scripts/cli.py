"""
Module cli.py

This module contains command-line interfaces for the verification of
neural networks properties in the VNN-LIB standard
(www.vnnlib.org/#standard)

Author: Stefano Demarchi

"""
import os

from pynever.networks import SequentialNetwork
from pynever.strategies import conversion
from pynever.strategies.conversion import ONNXNetwork, ONNXConverter
from pynever.strategies.smt_reading import SmtPropertyParser
from pynever.strategies.verification import NeVerProperty, NeverVerification


def show_help():
    print("usage: python never2.py ... [-verify] [args]")
    print()
    print("Options and arguments:")
    print("no args        : launch NeVer2 in GUI mode.")
    print("-verify args   : verify the VNN-LIB property in args[1] on the"
          "               : ONNX model in args[2]")
    print()
    print("args ...       : arguments passed to program in sys.argv[1:]")
    print()


def verify_model(property_file: str, model_file: str) -> bool:
    """
    This method starts the verification procedure on the network model
    provided in the model_file path and prints the result

    Parameters
    ----------
    property_file : str
        Path to the .vnnlib or .smt2 file of the property
    model_file : str
        Path to the .onnx file of the network

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

                    strategy = NeverVerification()
                    result = strategy.verify(network, to_verify)
                    print(f'Verification result: {result}')
                    return result
            else:
                print('The model is not an ONNX model.')
                return False
