import logging
import os
from typing import Callable

import pynever.datasets as dt
import torch
import torch.nn.functional as fun
import torch.optim as opt
import torchvision.transforms as tr
from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QVBoxLayout, QHBoxLayout, QGridLayout, QFileDialog
from pynever.datasets import Dataset
from pynever.networks import NeuralNetwork
from pynever.strategies import reading, verification
from pynever.strategies.training import PytorchTraining, PytorchMetrics

import never2.view.styles as style
from never2 import ROOT_DIR
from never2.view.util import utility
from never2.view.widget.custom import CustomLabel, CustomComboBox, CustomTextBox, CustomButton
from never2.view.widget.dialog.dialogs import MessageDialog, MessageType, GenericDatasetDialog, ArithmeticValidator, \
    MixedVerificationDialog
from never2.view.widget.misc import LoggerTextBox


class NeVerWindow(QtWidgets.QDialog):
    """
    Base class for grouping common elements of the windows.
    Each window shares a main layout (vertical by default),
    a title and a dictionary of combobox for the parameters.

    Attributes
    ----------
    layout : QVBoxLayout
        The main layout of the window.
    title : str
        Window title to display.
    widgets : dict
        The dictionary of the displayed widgets.

    Methods
    ----------
    render_layout()
        Procedure to display the window layout.
    create_widget_layout(str, dict, Callable, Callable)
        Procedure to display widgets from a dictionary.

    """

    def __init__(self, title="NeVer Window", parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout()
        self.title = title
        self.params = dict()
        self.widgets = dict()

        self.setWindowTitle(self.title)
        self.setModal(True)
        self.setStyleSheet("background-color: " + style.GREY_1 + ";")

    def render_layout(self) -> None:
        """
        This method updates the main_layout with the changes done
        in the child class(es).

        """

        self.setLayout(self.layout)

    def create_widget_layout(self, widget_dict: dict, cb_f: Callable = None, line_f: Callable = None) -> QHBoxLayout:
        """
        This method sets up the parameters layout by reading
        the JSON-based dict of params and building
        the corresponding graphic objects.

        Parameters
        ----------
        widget_dict : dict
            The dictionary of widgets to build.
        cb_f : Callable, optional
            The activation function for combo boxes.
        line_f : Callable, optional
            The activation function for text boxes.

        Returns
        ----------
        QHBoxLayout
            The layout with all the widgets loaded.

        """

        widget_layout = QHBoxLayout()
        left_layout = QGridLayout()
        left_layout.setAlignment(Qt.AlignTop)

        counter = 0
        for first_level in widget_dict.keys():

            sub_key = next(iter(widget_dict[first_level]))

            if type(widget_dict[first_level][sub_key]) == dict:

                self.widgets[first_level] = CustomComboBox()
                for second_level in widget_dict[first_level].keys():
                    self.widgets[first_level].addItem(second_level)
                self.widgets[first_level].setCurrentIndex(-1)

                if cb_f is not None:
                    self.widgets[first_level].activated.connect(cb_f(first_level))
            else:

                if widget_dict[first_level]["type"] == "bool":

                    self.widgets[first_level] = CustomComboBox()
                    self.widgets[first_level].addItems([str(widget_dict[first_level]["value"]),
                                                        str(not widget_dict[first_level]["value"])])
                else:

                    self.widgets[first_level] = CustomTextBox()
                    self.widgets[first_level].setText(str(widget_dict[first_level].get("value", "")))

                    if line_f is not None:
                        self.widgets[first_level].textChanged.connect(line_f(first_level))

                    if widget_dict[first_level]["type"] == "int":
                        self.widgets[first_level].setValidator(ArithmeticValidator.INT)
                    elif widget_dict[first_level]["type"] == "float":
                        self.widgets[first_level].setValidator(ArithmeticValidator.FLOAT)
                    elif widget_dict[first_level]["type"] == "tensor" or \
                            widget_dict[first_level]["type"] == "tuple":
                        self.widgets[first_level].setValidator(ArithmeticValidator.TENSOR)

            w_label = CustomLabel(first_level)
            if 'optional' in widget_dict[first_level].keys():
                w_label.setText(first_level + ' (opt)')
            w_label.setToolTip(widget_dict[first_level].get("description"))
            left_layout.addWidget(w_label, counter, 0)
            left_layout.addWidget(self.widgets[first_level], counter, 1)
            counter += 1

        widget_layout.addLayout(left_layout)
        return widget_layout


class TrainingWindow(NeVerWindow):
    """
    This class is a Window for the training of the network.
    It features a file picker for choosing the dataset and
    a grid of parameters for tuning the procedure.

    Attributes
    ----------
    nn : NeuralNetwork
        The current network used in the main window, to be
        trained with the parameters selected here.
    is_nn_trained : bool
        Flag signaling whether the training procedure succeeded
        or not.
    dataset_path : str
        The dataset path to train the network.
    dataset_params : dict
        Additional parameters for generic datasets.
    dataset_transform : Transform
        Transform on the dataset.
    gui_params : dict
        The dictionary of secondary parameters displayed
        based on the selection.
    grid_layout : QGridLayout
        The layout to display the GUI parameters on.

    Methods
    ----------
    clear_grid()
        Procedure to clear the grid layout.
    update_grid_view(str)
        Procedure to update the grid layout.
    show_layout(str)
        Procedure to display the grid layout.
    update_dict_value(str, str, str)
        Procedure to update the parameters.

    """

    def __init__(self, nn: NeuralNetwork):
        super().__init__("Train Network")

        # Training elements
        self.nn = nn
        self.is_nn_trained = False
        self.dataset_path = ""
        self.dataset_params = dict()
        self.dataset_transform = None
        self.params = utility.read_json(ROOT_DIR + '/res/json/training.json')
        self.gui_params = dict()
        self.loss_f = ''
        self.metric = ''
        self.grid_layout = QGridLayout()

        # Dataset
        dataset_layout = QHBoxLayout()
        self.widgets["dataset"] = CustomComboBox()
        self.widgets["dataset"].addItems(["MNIST", "Fashion MNIST", "Custom data source..."])
        self.widgets["dataset"].setCurrentIndex(-1)
        self.widgets["dataset"].activated \
            .connect(lambda: self.setup_dataset(self.widgets["dataset"].currentText()))
        dataset_layout.addWidget(CustomLabel("Dataset"))
        dataset_layout.addWidget(self.widgets["dataset"])
        self.layout.addLayout(dataset_layout)

        transform_layout = QHBoxLayout()
        self.widgets["transform"] = CustomComboBox()
        self.widgets["transform"] \
            .addItem("Compose(ToTensor, Normalize(1, 0.5), Flatten)")
        self.widgets["transform"].setCurrentIndex(-1)
        self.widgets["transform"].activated \
            .connect(lambda: self.setup_transform(self.widgets["transform"].currentText()))
        transform_layout.addWidget(CustomLabel("Dataset transform"))
        transform_layout.addWidget(self.widgets["transform"])
        self.layout.addLayout(transform_layout)

        # Separator
        sep_label = CustomLabel("Training parameters")
        sep_label.setAlignment(Qt.AlignCenter)
        sep_label.setStyleSheet(style.NODE_LABEL_STYLE)
        self.layout.addWidget(sep_label)

        # Main body
        # Activation functions for dynamic widgets
        def activation_combo(key: str):
            return lambda: self.update_grid_view(f"{key}:{self.widgets[key].currentText()}")

        def activation_line(key: str):
            return lambda: self.update_dict_value(key, "", self.widgets[key].text())

        body_layout = self.create_widget_layout(self.params, activation_combo, activation_line)
        body_layout.addLayout(self.grid_layout)
        self.grid_layout.setAlignment(Qt.AlignTop)
        self.layout.addLayout(body_layout)

        # Buttons
        btn_layout = QHBoxLayout()
        self.train_btn = CustomButton("Train network")
        self.train_btn.clicked.connect(self.train_network)
        self.cancel_btn = CustomButton("Cancel")
        self.cancel_btn.clicked.connect(self.close)
        btn_layout.addWidget(self.train_btn)
        btn_layout.addWidget(self.cancel_btn)
        self.layout.addLayout(btn_layout)

        self.render_layout()

    def clear_grid(self) -> None:
        """
        This method clears the grid view of the layout,
        in order to display fresh new infos.

        """

        for i in reversed(range(self.grid_layout.count())):
            self.grid_layout.itemAt(i).widget().deleteLater()

    def update_grid_view(self, caller: str) -> None:
        """
        This method updates the grid view of the layout,
        displaying the corresponding parameters to the
        selected parameter.

        Parameters
        ----------
        caller : str
            The parameter selected in the combo box.

        """

        self.clear_grid()
        if 'Loss Function' in caller:
            self.loss_f = caller
        elif 'Metrics' in caller:
            self.metric = caller

        for first_level in self.params.keys():
            if type(self.params[first_level]) == dict:
                for second_level in self.params[first_level].keys():
                    if caller == f"{first_level}:{second_level}" and caller not in self.gui_params:
                        self.gui_params[caller] = self.params[first_level][second_level]

        self.show_layout(caller)

    def show_layout(self, name: str) -> None:
        """
        This method displays a grid layout initialized by the
        dictionary of parameters and default values.

        Parameters
        ----------
        name : str
            The name of the main parameter to which
            the dictionary is related.

        """

        title = CustomLabel(name)
        title.setAlignment(Qt.AlignCenter)
        self.grid_layout.addWidget(title, 0, 0, 1, 2)
        widgets_2level = dict()

        count = 1
        for k, v in self.gui_params[name].items():
            # Activation functions for dynamic widgets
            def activation_combo(super_key: str, key: str):
                return lambda: self.update_dict_value(name,
                                                      key,
                                                      widgets_2level[f"{super_key}:{key}"][1].currentText())

            def activation_line(super_key: str, key: str):
                return lambda: self.update_dict_value(name,
                                                      key,
                                                      widgets_2level[f"{super_key}:{key}"][1].text())

            w_label = CustomLabel(k)
            w_label.setToolTip(v.get("description"))
            if v["type"] == "bool":
                cb = CustomComboBox()
                cb.addItems([str(v["value"]), str(not v["value"])])
                widgets_2level[f"{name}:{k}"] = (w_label, cb)
                widgets_2level[f"{name}:{k}"][1].activated.connect(activation_combo(name, k))
            elif "allowed" in v.keys():
                cb = CustomComboBox()
                cb.addItems(v["allowed"])
                widgets_2level[f"{name}:{k}"] = (w_label, cb)
                widgets_2level[f"{name}:{k}"][1].activated.connect(activation_combo(name, k))
            else:
                widgets_2level[f"{name}:{k}"] = (w_label, CustomTextBox(str(v["value"])))
                widgets_2level[f"{name}:{k}"][1].textChanged.connect(activation_line(name, k))
                if v["type"] == "int":
                    widgets_2level[f"{name}:{k}"][1].setValidator(ArithmeticValidator.INT)
                elif v["type"] == "float":
                    widgets_2level[f"{name}:{k}"][1].setValidator(ArithmeticValidator.FLOAT)
                elif v["type"] == "tensor" or \
                        v["type"] == "tuple":
                    widgets_2level[f"{name}:{k}"][1].setValidator(ArithmeticValidator.TENSOR)

            self.grid_layout.addWidget(widgets_2level[f"{name}:{k}"][0], count, 0)
            self.grid_layout.addWidget(widgets_2level[f"{name}:{k}"][1], count, 1)
            count += 1

    def update_dict_value(self, name: str, key: str, value: str) -> None:
        """
        This method updates the correct parameter based
        on the selection in the GUI. It provides the details
        to access the parameter and the new value to register.

        Parameters
        ----------
        name : str
            The learning parameter name, which is
            the key of the main dict.
        key : str
            The name of the parameter detail,
            which is the key of the second-level dict.
        value : str
            The new value for parameter[name][key].

        """

        # Cast type
        if name not in self.gui_params.keys():
            gui_param = self.params[name]
        else:
            gui_param = self.gui_params[name][key]

        if gui_param["type"] == "bool":
            value = value == "True"
        elif gui_param["type"] == "int" and value != "":
            value = int(value)
        elif gui_param["type"] == "float" and value != "":
            value = float(value)
        elif gui_param["type"] == "tuple" and value != "":
            value = eval(value)

        # Apply changes
        if ":" in name:
            first_level, second_level = name.split(":")
            self.params[first_level][second_level][key]["value"] = value
        else:
            self.params[name]["value"] = value

    def setup_dataset(self, name: str) -> None:
        """
        This method reacts to the selection of a dataset in the
        dataset combo box. Depending on the selection, the correct
        path is saved and any additional parameters are asked.

        Parameters
        ----------
        name : str
            The dataset name.

        """

        if name == "MNIST":
            self.dataset_path = ROOT_DIR + "/data/MNIST/"
        elif name == "Fashion MNIST":
            self.dataset_path = ROOT_DIR + "/data/fMNIST/"
        else:
            datapath = QFileDialog.getOpenFileName(None, "Select data source...", "")
            self.dataset_path = datapath[0]

            # Get additional parameters via dialog
            dialog = GenericDatasetDialog()
            dialog.exec()
            self.dataset_params = dialog.params

    def setup_transform(self, sel_t: str) -> None:
        if sel_t != '':
            self.dataset_transform = tr.Compose([tr.ToTensor(),
                                                 tr.Normalize(1, 0.5),
                                                 tr.Lambda(lambda x: torch.flatten(x))])

    def load_dataset(self) -> Dataset:
        """
        This method initializes the selected dataset object,
        given the path loaded before.

        Returns
        -------
        Dataset
            The dataset object.

        """
        if self.dataset_path == ROOT_DIR + "/data/MNIST/":
            return dt.TorchMNIST(self.dataset_path, True, self.dataset_transform)
        elif self.dataset_path == ROOT_DIR + "/data/fMNIST/":
            return dt.TorchFMNIST(self.dataset_path, True, self.dataset_transform)
        elif self.dataset_path != "":
            return dt.GenericFileDataset(self.dataset_path,
                                         self.dataset_params["target_idx"],
                                         self.dataset_params["data_type"],
                                         self.dataset_params["delimiter"],
                                         self.dataset_transform)

    def train_network(self):
        """
        This method reads the inout from the window widgets and
        launches the training procedure on the selected dataset.


        """

        err_dialog = None
        if self.dataset_path == "":
            err_dialog = MessageDialog("No dataset selected.", MessageType.ERROR)
        elif self.widgets["Optimizer"].currentIndex() == -1:
            err_dialog = MessageDialog("No optimizer selected.", MessageType.ERROR)
        elif self.widgets["Scheduler"].currentIndex() == -1:
            err_dialog = MessageDialog("No scheduler selected.", MessageType.ERROR)
        elif self.widgets["Loss Function"].currentIndex() == -1:
            err_dialog = MessageDialog("No loss function selected.", MessageType.ERROR)
        elif self.widgets["Metrics"].currentIndex() == -1:
            err_dialog = MessageDialog("No metrics selected.", MessageType.ERROR)
        elif "value" not in self.params["Epochs"].keys():
            err_dialog = MessageDialog("No epochs selected.", MessageType.ERROR)
        elif "value" not in self.params["Validation percentage"].keys():
            err_dialog = MessageDialog("No validation percentage selected.", MessageType.ERROR)
        elif "value" not in self.params["Training batch size"].keys():
            err_dialog = MessageDialog("No training batch size selected.", MessageType.ERROR)
        elif "value" not in self.params["Validation batch size"].keys():
            err_dialog = MessageDialog("No validation batch size selected.", MessageType.ERROR)
        if err_dialog is not None:
            err_dialog.exec()
            return

        # Load dataset
        data = self.load_dataset()

        # Add logger text box
        log_textbox = LoggerTextBox(self)
        logger = logging.getLogger("pynever.strategies.training")
        logger.addHandler(log_textbox)
        logger.setLevel(logging.INFO)
        self.layout.addWidget(log_textbox.widget)

        logger.info("***** NeVer 2 - TRAINING *****")

        # Create optimizer dictionary of parameters
        opt_params = dict()
        for k, v in self.gui_params["Optimizer:Adam"].items():
            opt_params[v["name"]] = v["value"]

        # Create scheduler dictionary of parameters
        sched_params = dict()
        for k, v in self.gui_params["Scheduler:ReduceLROnPlateau"].items():
            sched_params[v["name"]] = v["value"]

        # Init loss function
        if self.loss_f == "Loss Function:Cross Entropy":
            loss = fun.cross_entropy
            loss.weight = self.gui_params["Loss Function:Cross Entropy"]["Weight"]["value"]
            loss.ignore_index = self.gui_params["Loss Function:Cross Entropy"]["Ignore index"]["value"]
            loss.reduction = self.gui_params["Loss Function:Cross Entropy"]["Reduction"]["value"]
        else:
            loss = fun.mse_loss
            loss.reduction = self.gui_params["Loss Function:MSE Loss"]["Reduction"]["value"]

        # Init metrics
        if self.metric == "Metrics:Inaccuracy":
            metrics = PytorchMetrics.inaccuracy
        else:
            metrics = None  # TODO which is MSE metric?

        # Checkpoint loading
        checkpoint_path = None
        for fname in os.listdir('.'):
            if fname.endswith('.pth.tar'):
                checkpoint_path = fname
                break

        start_epoch = 0
        if checkpoint_path is not None:
            checkpoint = torch.load(checkpoint_path)
            start_epoch = checkpoint["epoch"]
            if self.params["Epochs"]["value"] <= start_epoch:
                start_epoch = -1
                logger.info("Checkpoint already reached, no further training necessary")

        if start_epoch > -1:
            # Init train strategy
            train_strategy = PytorchTraining(opt.Adam, opt_params,
                                             loss,
                                             self.params["Epochs"]["value"],
                                             self.params["Validation percentage"]["value"],
                                             self.params["Training batch size"]["value"],
                                             self.params["Validation batch size"]["value"],
                                             opt.lr_scheduler.ReduceLROnPlateau,
                                             sched_params,
                                             metrics,
                                             cuda=self.params["Cuda"]["value"],
                                             train_patience=self.params["Train patience"].get("value", None),
                                             checkpoints_root=self.params["Checkpoints root"].get("value", ''),
                                             verbose_rate=self.params["Verbosity level"].get("value", None))
            try:
                self.nn = train_strategy.train(self.nn, data)
                self.is_nn_trained = True
            except Exception as e:
                self.nn = None
                dialog = MessageDialog("Training error:\n" + str(e), MessageType.ERROR)
                dialog.exec()
                self.close()

        self.train_btn.setEnabled(False)
        self.cancel_btn.setText("Close")


class VerificationWindow(NeVerWindow):
    """
    This class is a Window for the verification of the network.
    It features a combo box for choosing the verification
    heuristic.

    """

    def __init__(self, nn: NeuralNetwork, properties: dict):
        super().__init__("Verify network")

        self.nn = nn
        self.properties = properties
        self.strategy = None

        self.params = utility.read_json(ROOT_DIR + '/res/json/verification.json')

        def activation_cb(methodology: str):
            return lambda: self.update_methodology(self.widgets["Verification methodology"].currentText())

        body_layout = self.create_widget_layout(self.params, cb_f=activation_cb)
        self.layout.addLayout(body_layout)

        # Buttons
        btn_layout = QHBoxLayout()
        self.verify_btn = CustomButton("Verify network")
        self.verify_btn.clicked.connect(self.verify_network)
        self.cancel_btn = CustomButton("Cancel")
        self.cancel_btn.clicked.connect(self.close)
        btn_layout.addWidget(self.verify_btn)
        btn_layout.addWidget(self.cancel_btn)
        self.layout.addLayout(btn_layout)

        self.render_layout()

    def update_methodology(self, methodology: str) -> None:
        if methodology == 'Complete':
            self.strategy = verification.NeverVerification(heuristic="best_n_neurons", params=[10000])
        elif methodology == 'Over-approximated':
            self.strategy = verification.NeverVerification(heuristic="best_n_neurons", params=[0])
        else:
            dialog = MixedVerificationDialog()
            dialog.exec()
            self.strategy = verification.NeverVerification(heuristic="best_n_neurons", params=[dialog.n_neurons])

    def verify_network(self):
        """
        This class is a Window for the training of the network.
        It features a file picker for choosing the dataset and
        a grid of parameters for tuning the procedure.

        """

        if self.strategy is None:
            err_dialog = MessageDialog("No verification methodology selected.", MessageType.ERROR)
            err_dialog.exec()
            return

        # Save properties
        path = 'never2/' + self.__repr__().split(' ')[-1].replace('>', '') + '.smt2'
        utility.write_smt_property(path, self.properties, 'Real')

        input_name = list(self.properties.keys())[0]
        output_name = list(self.properties.keys())[-1]

        # Add logger text box
        log_textbox = LoggerTextBox(self)
        logger = logging.getLogger("pynever.strategies.verification")
        logger.addHandler(log_textbox)
        logger.setLevel(logging.INFO)
        self.layout.addWidget(log_textbox.widget)

        logger.info("***** NeVer 2 - VERIFICATION *****")

        # Load NeVerProperty from file
        parser = reading.SmtPropertyParser(verification.SMTLIBProperty(path), input_name, output_name)
        to_verify = parser.parse_property()

        # Property read, delete file
        os.remove(path)

        # Launch verification
        self.strategy.verify(self.nn, to_verify)
        self.verify_btn.setEnabled(False)
        self.cancel_btn.setText("Close")
