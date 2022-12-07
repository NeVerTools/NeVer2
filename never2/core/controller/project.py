import pynever.networks as pynn
import pynever.strategies.conversion as conv
from PyQt5.QtCore import pyqtSignal, QObject, Qt
from PyQt5.QtWidgets import QFileDialog, QApplication
from pynever.strategies.conversion import ONNXNetwork, \
    ONNXConverter, PyTorchConverter, TensorflowConverter, PyTorchNetwork, TensorflowNetwork, AlternativeRepresentation
from pynever.strategies.smt_reading import ExpressionTreeConverter
from pysmt.exceptions import PysmtException
from pysmt.smtlib.parser import SmtLibParser

from never2.view.drawing.element import PropertyBlock
from never2.view.util import utility
from never2.view.widget.dialog.dialogs import MessageDialog, MessageType, InputDialog

# Formats available for opening and saving networks
NETWORK_FORMATS_OPENING = "All supported formats (*.onnx *.pt *.pth);;\
                            ONNX (*.onnx);;\
                            PyTorch (*.pt *.pth)"
NETWORK_FORMATS_SAVE = "ONNX (*.onnx);;\
                        PyTorch (*.pt *.pth);;\
                        VNNLIB (*.onnx + *.smt2)"
PROPERTY_FORMATS = "VNN-LIB files (*.smt *.smt2 *.vnnlib);;\
                           SMT (*.smt *.smt2);;\
                           VNNLIB (*.vnnlib)"
SUPPORTED_NETWORK_FORMATS = {'VNNLIB': ['vnnlib'],
                             'ONNX': ['onnx'],
                             'PyTorch': ['pt', 'pth']}
SUPPORTED_PROPERTY_FORMATS = {'SMT': ['smt', 'smt2'],
                              'VNNLIB': ['vnnlib']}


class Project(QObject):
    """
    This class manages the opened network by handling file saving and opening,
    and the conversion to/from the internal representation.

    Attributes
    ----------
    file_name : (str, str)
        The file name of the network, wrapped in a tuple (name, extension)
    network : NeuralNetwork
        The current sequential network.
    properties : dict
        Dictionary mapping properties to nodes.
    input_handler : InputHandler
        It is instantiated to open and convert a network from a file.
    output_handler : OutputHandler
        It is instantiated to save and convert a network in a file.

    Methods
    ----------
    open()
        This method opens a file converting the network in the internal
        representation.
    save(bool)
        This method saves a file in the desired format.

    """

    # This signal will be connected to the canvas to draw the opened network.
    opened_net = pyqtSignal()
    opened_property = pyqtSignal()

    def __init__(self):
        super(QObject, self).__init__()
        self.file_name = ("", "")

        self.network = pynn.SequentialNetwork("", "X")
        self.properties = dict()

        self.input_handler = None
        self.output_handler = None

    def open(self):
        """
        This method opens a file for reading a network in one of the supported
        formats. The network is then converted by a thread, while a
        loading dialog is displayed.

        """

        # Open network
        self.file_name = QFileDialog.getOpenFileName(None, "Open network", "", NETWORK_FORMATS_OPENING)

        # If a file has been selected:
        if self.file_name != ("", ""):
            self.input_handler = InputHandler()

            # A "wait cursor" appears
            QApplication.setOverrideCursor(Qt.WaitCursor)
            self.network = self.input_handler.read_network(self.file_name[0])
            if isinstance(self.network, pynn.SequentialNetwork) and \
                    self.network.input_id == '':
                self.network.input_id = 'X'
            QApplication.restoreOverrideCursor()

            # At the end of the loading, the main thread looks for potential
            # exceptions in the input_handler
            if self.input_handler.conversion_exception is not None:
                # If there is some error in converting, it is returned
                # an error message
                error_dialog = MessageDialog("Error in network reading: \n"
                                             + str(self.input_handler.conversion_exception),
                                             MessageType.ERROR)
                error_dialog.exec()
            else:
                self.opened_net.emit()

    def open_property(self):
        """
        This method opens a SMT file containing the description
        of the network properties. The file is checked to be
        consistent with the network and then parsed in order
        to build the property objects.

        Returns
        -------

        """
        # Check project
        if not self.network.nodes:
            err = MessageDialog("No network loaded!", MessageType.ERROR)
            err.exec()
            return

        # Select file
        property_file_name = QFileDialog.getOpenFileName(None, "Open property file", "", PROPERTY_FORMATS)

        if property_file_name != ("", ""):
            self.input_handler = InputHandler()

            QApplication.setOverrideCursor(Qt.WaitCursor)
            self.properties = read_properties(property_file_name[0])
            QApplication.restoreOverrideCursor()
            self.opened_property.emit()

    def save(self, _as: bool = True):
        """
        This method converts and saves the network in a file.
        It prompts the user before starting.

        Parameters
        ----------
        _as : bool
            This attribute distinguishes between "save" and "save as".
            If _as is True the network will be saved in a new file, while
            if _as is False the network will overwrite the current one.

        """

        # If the user picked "save as" option or there isn't a current file,
        # a dialog is opened to chose where to save the net
        if _as or self.file_name == ("", ""):
            self.file_name = QFileDialog.getSaveFileName(None, 'Save File', "", NETWORK_FORMATS_SAVE)

        if self.file_name != ("", ""):
            self.output_handler = OutputHandler()
            self.network.identifier = self.file_name[0].split('/')[-1].split(".")[0]

            # A  "wait cursor" appears locking the interface
            QApplication.setOverrideCursor(Qt.WaitCursor)
            self.output_handler.save(self.network, self.file_name)
            if self.properties:
                self.output_handler.save_properties(self.properties, self.file_name)
            QApplication.restoreOverrideCursor()

            # At the end of the loading, the main thread looks for eventual
            # Exception in the output_handler
            if self.output_handler.exception is not None:
                error_dialog = MessageDialog("Error in network saving: \n"
                                             + str(self.output_handler.exception),
                                             MessageType.ERROR)
                error_dialog.exec()


def read_properties(path: str) -> dict:
    """
    This method reads the SMT property file and
    creates a property for each node.

    Parameters
    ----------
    path : str
        The SMT-LIB file path.

    Returns
    -------
    dict
        The dictionary of properties

    """

    parser = SmtLibParser()
    try:
        script = parser.get_script_fname(path)
    except PysmtException:
        dialog = MessageDialog("Failed to parse SMT property.", MessageType.ERROR)
        dialog.exec()
        return dict()

    declarations = script.filter_by_command_name(['declare-fun', 'declare-const'])
    assertions = script.filter_by_command_name('assert')
    var_set = []
    var_list = []
    properties = dict()

    for d in declarations:
        var_list.append(str(d.args[0]).replace('\'', ''))
        varname = str(d.args[0]).split('_')[0].replace('\'', '')  # Variable format is <v_name>_<idx>
        if varname not in var_set:
            var_set.append(varname)

    counter = 0

    for a in assertions:
        line = str(a.args[0]).replace('\'', '')
        for v in var_set:
            if f" {v}" in line or f"({v}" in line:  # Either '(v ...' or '... v)'
                if v not in properties.keys():
                    properties[v] = PropertyBlock(f"{counter}Pr", "Generic SMT")
                    properties[v].smt_string = ''
                    properties[v].variables = list(filter(lambda x: v in x, var_list))
                    counter += 1
                conv = ExpressionTreeConverter()
                wrap = conv.build_from_infix(line).as_prefix()
                properties[v].smt_string += f"(assert {wrap})\n"
                break

    return properties


class InputHandler:
    """
    This class provides an interface for reading a file containing a
    NeuralNetwork and converting it in the internal representation.

    Attributes
    ----------
    extension : str
        Format of the network.
    alt_repr : AlternativeRepresentation
        Network in original format.
    network_input : tuple
        Optional input of the network.
    strategy : ConversionStrategy
        Converter from an alternative representation.
    input_exception : Exception
        Optional exception in the input stage.
    conversion_exception : Exception
        Optional exception in the conversion stage.

    Methods
    ----------
    read_network(str)
        Procedure to read and convert the network in the
        internal representation.
    read_input_dialog()
        Procedure to open a dialog and get an input for
        the network.
    set_input_shape(tuple)
        Procedure to apply an input shape.

    """

    def __init__(self):
        self.extension = ""
        self.alt_repr = None
        self.network_input = None
        self.strategy = None

        self.input_exception = None
        self.conversion_exception = None

    def read_network(self, path: str) -> pynn.NeuralNetwork:
        """
        This method converts the network from the file to an alternative
        representation.

        Parameters
        ----------
        path : str
            The network file path.

        Returns
        ----------
        NeuralNetwork
            The internal representation of the converted network.

        """

        if path == "":
            raise Exception("Invalid path.")

        # Get extension
        self.extension = path.split(".")[-1]
        self.alt_repr = conv.load_network_path(path)

        # Convert the network
        if self.alt_repr is not None:
            try:
                # Converting the network in the internal representation
                # If the chosen format has got an initial input for the network,
                # it is converted in the internal representation
                if isinstance(self.alt_repr, ONNXNetwork):
                    self.strategy = ONNXConverter()
                else:
                    self.strategy = PyTorchConverter()

                return self.strategy.to_neural_network(self.alt_repr)

            except Exception as e:
                # Even in case of conversion_exception, the signal of the ending of the
                # ending is emitted in order to update the interface
                self.conversion_exception = e
        else:
            self.conversion_exception = Exception("Error in network reading.")

    def read_input_dialog(self) -> tuple:
        """
        This method allows the user to define the input shape of the network
        before opening.

        Returns
        ----------
        tuple
            The input shape given by the user.

        """

        dialog_text = "Please, give an input shape for the network."
        if self.input_exception is not None:
            dialog_text += "\n" + str(self.input_exception)

        input_dialog = InputDialog(dialog_text)

        # The cursor is restored to use the dialog
        QApplication.restoreOverrideCursor()
        input_dialog.exec()
        QApplication.setOverrideCursor(Qt.WaitCursor)

        if input_dialog.input is not None:
            # Pass input to input_handler and open
            return input_dialog.input

    def set_input_shape(self, input_shape: tuple) -> pynn.NeuralNetwork:
        """
        This method is called when an input for the network is required, and
        not provided by the original format. The network is converted starting
        from that input.

        Parameters
        ----------
        input_shape : tuple
            The provided shape.

        Returns
        ----------
        NeuralNetwork
            The network with the new input shape.

        """

        try:
            if input_shape is None:
                raise Exception("Can't open the network without a valid input")

            # Select the format
            if isinstance(self.alt_repr, PyTorchNetwork):
                self.strategy = PyTorchConverter()

            elif isinstance(self.alt_repr, TensorflowNetwork):
                self.strategy = TensorflowConverter()

            # Converting the network with the given input
            return self.strategy.to_neural_network(self.alt_repr)

        except Exception as e:
            # If the input is not correct, an conversion_exception is saved and an interaction
            # with the user is required again
            self.input_exception = e


class OutputHandler:
    """
    This class converts and saves the network in one of the supported
    formats.

    Attributes
    ----------
    extension : str
        Extension of the network to save.
    alt_repr : AlternativeRepresentation
        Converted representation of the network
        to save.
    exception : Exception
        Exception to handle at the upper level
    strategy : ConversionStrategy
        Converter for the chosen format

    Methods
    ----------
    save(NeuralNetwork, tuple)
        Saves the network with the given name and format.
    convert_network()
        Converts the network in the desired format.

    """

    def __init__(self):
        self.extension = None
        self.alt_repr = None
        self.exception = None
        self.strategy = None

    def save(self, network: pynn.NeuralNetwork, filename: tuple) -> None:
        """
        This method converts the current network and saves it in the chosen
        format.

        """

        if '.' not in filename[0]:  # If no explicit extension
            if 'VNNLIB' in filename[1]:
                self.extension = 'vnnlib'
            if self.extension == 'vnnlib':
                filename = (f"{filename[0]}.onnx", filename[1])
            else:
                self.extension = filename[0].split(".")[-1]
                filename = (f"{filename[0]}.{self.extension}", filename[1])
        else:
            self.extension = filename[0].split('.')[-1]

        try:
            # The network is converted in the alternative representation
            self.alt_repr = self.convert_network(network, filename[0])

            # Saving the network on file depending on the format
            conv.save_network_path(self.alt_repr, filename[0])

        except Exception as e:
            self.exception = e

    def save_properties(self, properties: dict, filename: tuple) -> None:
        """
        This method saves the properties in the network as a SMT-LIB
        file. The file shares the same name as the network file, with
        the changed extension.

        Parameters
        ----------
        properties : dict
            The dictionary of defined properties.
        filename : tuple
            The tuple containing the file name and the extension.

        """

        path = filename[0].replace("." + self.extension, ".smt2")
        if '.' not in path:
            path = path + '.smt2'

        # Update extension
        self.extension = "smt2"
        utility.write_smt_property(path, properties, 'Real')

    def convert_network(self, network: pynn.NeuralNetwork, filename: str) -> AlternativeRepresentation:
        """
        This method converts the internal representation into the chosen
        alternative representation, depending on the extension

        Attributes
        ----------
        network : NeuralNetwork
            The network to convert.
        filename : str
            The file name of the network.

        Returns
        ----------
        AlternativeRepresentation
            The converted network in the required extension.

        """

        # Getting the filename
        net_id = filename.split("/")[-1].split(".")[0]

        if self.extension in SUPPORTED_NETWORK_FORMATS['ONNX'] or \
                self.extension in SUPPORTED_NETWORK_FORMATS['VNNLIB']:
            self.strategy = ONNXConverter()
            model = self.strategy.from_neural_network(network)
            self.alt_repr = ONNXNetwork(net_id, model, True).onnx_network

        elif self.extension in SUPPORTED_NETWORK_FORMATS['PyTorch']:
            self.strategy = PyTorchConverter()
            self.alt_repr = self.strategy.from_neural_network(network)
            self.alt_repr.identifier = net_id
            self.alt_repr.up_to_date = True
        else:
            raise Exception("Format not supported")

        network.alt_rep_cache.append(self.alt_repr)
        return self.alt_repr
