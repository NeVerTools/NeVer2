"""
Module window.py

This module contains the classes for displaying the windows launching NeVer's capabilities
of learning and verification.

Author: Stefano Demarchi

"""
import logging
import os
from typing import Callable

import pynever.datasets as dt
import torch
import torch.nn.functional as fun
import torch.optim as opt
import torchvision.transforms as tr
from PyQt6 import QtWidgets
from PyQt6.QtCore import Qt, QObject, pyqtSignal, QThread
from PyQt6.QtWidgets import QVBoxLayout, QHBoxLayout, QGridLayout, QFileDialog
from pynever.datasets import Dataset
from pynever.networks import NeuralNetwork, SequentialNetwork
from pynever.strategies.training import PytorchTraining, PytorchMetrics, PytorchTesting
from pynever.strategies.verification.algorithms import SSLPVerification, SSBPVerification
from pynever.strategies.verification.parameters import SSLPVerificationParameters, \
    SSBPVerificationParameters
from pynever.strategies.verification.properties import VnnLibProperty
from pynever.strategies.verification.ssbp.constants import RefinementStrategy, BoundsBackend, IntersectionStrategy, \
    BoundsDirection

from never2 import RES_DIR, ROOT_DIR
from never2.resources.styling.custom import CustomComboBox, CustomTextBox, CustomLabel, CustomButton, \
    CustomLoggingHandler, CustomLoggerTextArea
from never2.utils import rep, file
from never2.utils.validator import ArithmeticValidator
from never2.view.ui.dialogs.action import ComposeTransformDialog
from never2.view.ui.dialogs.dialog import GenericDatasetDialog
from never2.view.ui.dialogs.message import MessageDialog, MessageType
from never2.view.ui.dialogs.tabs import VerificationTabWidget


class Params:
    """Static parameters used as keys for training parameters"""

    OPTIMIZER = 'Optimization algorithm'
    SCHEDULER = 'Learning rate scheduling'
    LOSS = 'Loss function measure'
    PRECISION = 'Precision Metric'


class AsyncWorker(QObject):
    """A class to run a task using a separate worker"""
    finished = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, task: Callable, params: tuple = None):
        super().__init__()
        self.task = task
        self.params = params

    def run(self):
        try:
            self.task(*self.params)
            self.finished.emit()
        except Exception as e:
            self.error.emit(str(e))


class BaseWindow(QtWidgets.QDialog):
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

    def __init__(self, title='Window', parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout()
        self.title = title
        self.params = dict()
        self.widgets = dict()

        self.setWindowTitle(self.title)
        self.setModal(True)

        # apply same QLineEdit and QComboBox style of the block contents
        qss_file = open(RES_DIR + '/styling/qss/blocks.qss').read()
        self.setStyleSheet(qss_file)

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
        left_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        counter = 0
        for first_level in widget_dict.keys():

            sub_key = next(iter(widget_dict[first_level]))

            if isinstance(widget_dict[first_level][sub_key], dict):

                self.widgets[first_level] = CustomComboBox()
                for second_level in widget_dict[first_level].keys():
                    self.widgets[first_level].addItem(second_level)
                self.widgets[first_level].setCurrentIndex(-1)

                if cb_f is not None:
                    self.widgets[first_level].activated.connect(cb_f(first_level))
            else:

                if widget_dict[first_level]['type'] == 'bool':

                    self.widgets[first_level] = CustomComboBox()
                    self.widgets[first_level].addItems([str(widget_dict[first_level]['value']),
                                                        str(not widget_dict[first_level]['value'])])
                else:

                    self.widgets[first_level] = CustomTextBox()
                    self.widgets[first_level].setText(str(widget_dict[first_level].get('value', '')))

                    if line_f is not None:
                        self.widgets[first_level].textChanged.connect(line_f(first_level))

                    if widget_dict[first_level]['type'] == 'int':
                        self.widgets[first_level].setValidator(ArithmeticValidator.INT)
                    elif widget_dict[first_level]['type'] == 'float':
                        self.widgets[first_level].setValidator(ArithmeticValidator.FLOAT)
                    elif widget_dict[first_level]['type'] == 'tensor' or \
                            widget_dict[first_level]['type'] == 'tuple':
                        self.widgets[first_level].setValidator(ArithmeticValidator.TENSOR)

            w_label = CustomLabel(first_level)

            if 'optional' not in widget_dict[first_level].keys():
                w_label.setText(first_level + '*')

            w_label.setToolTip(widget_dict[first_level].get('description'))
            left_layout.addWidget(w_label, counter, 0)
            left_layout.addWidget(self.widgets[first_level], counter, 1)
            counter += 1

        widget_layout.addLayout(left_layout)
        return widget_layout


class TrainingWindow(BaseWindow):
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
    testset_path : str
        The testset path to test the network.
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
    setup_dataset(str)
        Procedure to prepare the dataset loading.
    setup_testset(str)
        Procedure to prepare the testset loading.
    setup_transform(str)
        Procedure to add a transform to the dataset.
    load_dataset(bool)
        Procedure to load the dataset.
    execute_training()
        Procedure to launch the training.

    """

    def __init__(self, nn: SequentialNetwork):
        super().__init__('Train Network')

        # Training elements
        self.nn = nn
        self.is_nn_trained = False
        self.dataset_path = ''
        self.testset_path = ''
        self.dataset_params = dict()
        self.dataset_transform = tr.Compose([])
        self.params = rep.read_json(RES_DIR + '/json/training.json')
        self.gui_params = dict()
        self.loss_f = ''
        self.metric = ''
        self.grid_layout = QGridLayout()

        # Dataset
        dt_label = CustomLabel('Dataset', primary=True)
        self.layout.addWidget(dt_label)

        dataset_layout = QHBoxLayout()
        self.widgets['dataset'] = CustomComboBox()
        self.widgets['dataset'].addItems(['MNIST', 'Fashion MNIST', 'Custom data source...'])
        self.widgets['dataset'].setCurrentIndex(-1)
        self.widgets['dataset'].activated \
            .connect(lambda: self.setup_dataset(self.widgets['dataset'].currentText()))
        dataset_layout.addWidget(CustomLabel('Training set'))
        dataset_layout.addWidget(self.widgets['dataset'])

        self.widgets['testset'] = CustomComboBox()
        self.widgets['testset'].addItems(['MNIST', 'Fashion MNIST', 'Custom data source...'])
        self.widgets['testset'].setCurrentIndex(-1)
        self.widgets['testset'].activated \
            .connect(lambda: self.setup_testset(self.widgets['testset'].currentText()))
        dataset_layout.addWidget(CustomLabel('Test set'))
        dataset_layout.addWidget(self.widgets['testset'])

        self.layout.addLayout(dataset_layout)

        transform_layout = QHBoxLayout()
        self.widgets['transform'] = CustomComboBox()
        self.widgets['transform'].addItems(['No transform', 'Convolutional MNIST', 'Fully Connected MNIST',
                                            'Custom...'])
        self.widgets['transform'].activated \
            .connect(lambda: self.setup_transform(self.widgets['transform'].currentText()))
        transform_layout.addWidget(CustomLabel('Dataset transform'))
        transform_layout.addWidget(self.widgets['transform'])
        self.layout.addLayout(transform_layout)

        # Separator
        sep_label = CustomLabel('Training parameters', primary=True)
        self.layout.addWidget(sep_label)

        # Main body
        # Activation functions for dynamic widgets
        def activation_combo(key: str):
            return lambda: self.update_grid_view(f'{key}:{self.widgets[key].currentText()}')

        def activation_line(key: str):
            return lambda: self.update_dict_value(key, '', self.widgets[key].text())

        body_layout = self.create_widget_layout(self.params, activation_combo, activation_line)
        body_layout.addLayout(self.grid_layout)
        self.grid_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.layout.addLayout(body_layout)

        # Buttons
        btn_layout = QHBoxLayout()
        self.cancel_btn = CustomButton('Cancel')
        self.cancel_btn.clicked.connect(self.close)
        self.train_btn = CustomButton('Train network', primary=True)
        self.train_btn.clicked.connect(self.execute_training)
        btn_layout.addWidget(self.cancel_btn)
        btn_layout.addWidget(self.train_btn)
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
        if Params.LOSS in caller:
            self.loss_f = caller
        elif Params.PRECISION in caller:
            self.metric = caller

        for first_level in self.params.keys():
            if type(self.params[first_level]) == dict:
                for second_level in self.params[first_level].keys():
                    if caller == f'{first_level}:{second_level}' and caller not in self.gui_params:
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

        title = CustomLabel(name.replace(':', ': '))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.grid_layout.addWidget(title, 0, 0, 1, 2)
        widgets_2level = dict()

        count = 1
        for k, v in self.gui_params[name].items():
            # Activation functions for dynamic widgets
            def activation_combo(super_key: str, key: str):
                return lambda: self.update_dict_value(name,
                                                      key,
                                                      widgets_2level[f'{super_key}:{key}'][1].text())

            def activation_line(super_key: str, key: str):
                return lambda: self.update_dict_value(name,
                                                      key,
                                                      widgets_2level[f'{super_key}:{key}'][1].text())

            w_label = CustomLabel(k)
            w_label.setToolTip(v.get('description'))
            if v['type'] == 'bool':
                cb = CustomComboBox()
                cb.addItems([str(v['value']), str(not v['value'])])
                cb.activated.connect(activation_combo(name, k))
                widgets_2level[f'{name}:{k}'] = (w_label, cb)
            elif 'allowed' in v.keys():
                cb = CustomComboBox()
                cb.addItems(v['allowed'])
                cb.activated.connect(activation_combo(name, k))
                widgets_2level[f'{name}:{k}'] = (w_label, cb)
            else:
                tb = CustomTextBox(str(v['value']))
                tb.textChanged.connect(activation_line(name, k))

                if v['type'] == 'int':
                    tb.setValidator(ArithmeticValidator.INT)
                elif v['type'] == 'float':
                    tb.setValidator(ArithmeticValidator.FLOAT)
                elif v['type'] == 'tensor' or \
                        v['type'] == 'tuple':
                    tb.setValidator(ArithmeticValidator.TENSOR)

                widgets_2level[f'{name}:{k}'] = (w_label, tb)

            self.grid_layout.addWidget(widgets_2level[f'{name}:{k}'][0], count, 0)
            self.grid_layout.addWidget(widgets_2level[f'{name}:{k}'][1], count, 1)
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

        if gui_param['type'] == 'bool':
            value = value == 'True'
        elif gui_param['type'] == 'int' and value != '':
            value = int(value)
        elif gui_param['type'] == 'float' and value != '':
            value = float(value)
        elif gui_param['type'] == 'tuple' and value != '':
            value = eval(value)

        # Apply changes
        if ':' in name:
            first_level, second_level = name.split(':')
            self.params[first_level][second_level][key]['value'] = value
        else:
            self.params[name]['value'] = value

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

        match name:
            case 'MNIST':
                self.dataset_path = ROOT_DIR + '/data/MNIST/'
            case 'Fashion MNIST':
                self.dataset_path = ROOT_DIR + '/data/fMNIST/'
            case _:
                datapath = QFileDialog.getOpenFileName(None, 'Select data source...', '')
                self.dataset_path = datapath[0]

                # Get additional parameters via dialog
                if self.dataset_path != '':
                    dialog = GenericDatasetDialog()
                    dialog.exec()
                    self.dataset_params = dialog.params

    def setup_testset(self, name: str) -> None:
        """
        This method reacts to the selection of a test set in the
        testset combo box. Depending on the selection, the correct
        path is saved and any additional parameters are asked.

        Parameters
        ----------
        name : str
            The test set name.

        """

        match name:
            case 'MNIST':
                self.testset_path = ROOT_DIR + '/data/MNIST/'
            case 'Fashion MNIST':
                self.testset_path = ROOT_DIR + '/data/fMNIST/'
            case _:
                datapath = QFileDialog.getOpenFileName(None, 'Select data source...', '')
                self.testset_path = datapath[0]

    def setup_transform(self, sel_t: str) -> None:
        """
        This method prepares the dataset transform based on the user choice

        Parameters
        ----------
        sel_t : str
            Option selected by the user

        """

        match sel_t:
            case 'No transform':
                self.dataset_transform = tr.Compose([])
            case 'Convolutional MNIST':
                self.dataset_transform = tr.Compose([tr.ToTensor(), tr.Normalize(1, 0.5)])
            case 'Fully Connected MNIST':
                self.dataset_transform = tr.Compose([tr.ToTensor(),
                                                     tr.Normalize(1, 0.5),
                                                     tr.Lambda(lambda x: torch.flatten(x))])
            case _:
                dialog = ComposeTransformDialog()
                dialog.exec()
                self.dataset_transform = tr.Compose(dialog.trList)

    def load_dataset(self, train: bool = True) -> Dataset | None:
        """
        This method initializes the selected dataset object,
        given the path loaded before.

        Parameters
        ----------
        train : bool
            Flag to load the training set or the test set.

        Returns
        ----------
        Dataset | None
            The dataset object, if loaded correctly.

        """

        path = self.dataset_path if train else self.testset_path

        match path:
            case x if x == f'{ROOT_DIR}/data/MNIST/':
                return dt.TorchMNIST(path, train, self.dataset_transform)
            case x if x == f'{ROOT_DIR}/data/fMNIST/':
                return dt.TorchFMNIST(path, train, self.dataset_transform)
            case _:
                return dt.GenericFileDataset(path,
                                             self.nn.get_input_len(),
                                             self.dataset_params['data_type'],
                                             self.dataset_params['delimiter'],
                                             self.dataset_transform)

    def execute_training(self) -> None:
        """
        This method reads the inout from the window widgets and
        launches the training procedure on the selected dataset.

        """

        err_message = ''

        if not self.dataset_path:
            err_message = 'No dataset selected.'
        elif not self.testset_path:
            err_message = 'No test set selected.'
        elif self.widgets[Params.OPTIMIZER].currentIndex() == -1:
            err_message = 'No optimizer selected.'
        elif self.widgets[Params.SCHEDULER].currentIndex() == -1:
            err_message = 'No scheduler selected.'
        elif self.widgets[Params.LOSS].currentIndex() == -1:
            err_message = 'No loss function selected.'
        elif self.widgets[Params.PRECISION].currentIndex() == -1:
            err_message = 'No metrics selected.'
        elif 'value' not in self.params['Epochs'].keys():
            err_message = 'No epochs selected.'
        elif 'value' not in self.params['Validation percentage'].keys():
            err_message = 'No validation percentage selected.'
        elif 'value' not in self.params['Training batch size'].keys():
            err_message = 'No training batch size selected.'
        elif 'value' not in self.params['Validation batch size'].keys():
            err_message = 'No validation batch size selected.'

        if err_message:
            err_dialog = MessageDialog(err_message, MessageType.ERROR)
            err_dialog.exec()
            self.close()

        # Load dataset
        training_data = self.load_dataset()
        test_data = self.load_dataset(train=False)

        # Add logger dialog
        log_textbox = CustomLoggerTextArea(self)
        handler = CustomLoggingHandler()
        handler.log_signal.connect(log_textbox.appendPlainText)
        self.layout.addWidget(log_textbox)

        logger = logging.getLogger('pynever.strategies.training')
        logger.setLevel(logging.INFO)
        logger.addHandler(handler)

        logger.info('***** NeVer 2 - TRAINING *****')

        # Create optimizer dictionary of parameters
        opt_name = self.widgets[Params.OPTIMIZER].currentText()
        opt_params = dict()
        for k, v in self.gui_params[f'{Params.OPTIMIZER}:{opt_name}'].items():
            opt_params[v['name']] = v['value']

        match opt_name:
            case 'Adam':
                optimizer = opt.Adam
            case 'SGD':
                optimizer = opt.SGD
            case _:
                optimizer = opt.Adam

        # Create scheduler dictionary of parameters
        sched_name = self.widgets[Params.SCHEDULER].currentText()
        sched_params = dict()
        for k, v in self.gui_params[f'{Params.SCHEDULER}:{sched_name}'].items():
            sched_params[v['name']] = v['value']

        match sched_name:
            case 'ReduceLROnPlateau':
                scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau
            case 'LRScheduler':
                scheduler = torch.optim.lr_scheduler.LRScheduler
            case 'StepLR':
                scheduler = torch.optim.lr_scheduler.StepLR
            case _:
                scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau

        # Init loss function
        if self.loss_f == f'{Params.LOSS}:Cross Entropy':
            loss = torch.nn.CrossEntropyLoss()
            if self.gui_params[f'{Params.LOSS}:Cross Entropy']['Weight']['value'] != '':
                loss.weight = self.gui_params[f'{Params.LOSS}:Cross Entropy']['Weight']['value']
            loss.ignore_index = self.gui_params[f'{Params.LOSS}:Cross Entropy']['Ignore index']['value']
            loss.reduction = self.gui_params[f'{Params.LOSS}:Cross Entropy']['Reduction']['value']
        else:
            loss = fun.mse_loss
            loss.reduction = self.gui_params[f'{Params.LOSS}:MSE Loss']['Reduction']['value']

        # Init metrics
        if self.metric == f'{Params.PRECISION}:Inaccuracy':
            metrics = PytorchMetrics.inaccuracy
        else:
            metrics = fun.mse_loss
            metrics.reduction = self.gui_params[f'{Params.PRECISION}:MSE Loss']['Reduction']['value']

        # Checkpoint loading
        checkpoints_path = self.params['Checkpoints root'].get('value', '') + self.nn.identifier + '.pth.tar'
        if not os.path.isfile(checkpoints_path):
            checkpoints_path = None

        start_epoch = 0
        if checkpoints_path is not None:
            checkpoint = torch.load(checkpoints_path)
            start_epoch = checkpoint['epoch']
            if self.params['Epochs']['value'] <= start_epoch:
                start_epoch = -1
                logger.info('Checkpoint already reached, no further training necessary')

        if start_epoch > -1:
            # Init train strategy
            cuda_device = 'cuda' if self.params['Cuda']['value'] == 'True' else 'cpu'
            train_strategy = PytorchTraining(optimizer, opt_params,
                                             loss,
                                             self.params['Epochs']['value'],
                                             self.params['Validation percentage']['value'] / 100,
                                             self.params['Training batch size']['value'],
                                             self.params['Validation batch size']['value'], True,
                                             scheduler, sched_params,
                                             metrics, device=cuda_device,
                                             train_patience=self.params['Train patience'].get('value', None),
                                             checkpoints_root=self.params['Checkpoints root'].get('value', ''),
                                             verbose_rate=self.params['Verbosity level'].get('value', None))
            test_strategy = PytorchTesting(metrics, dict(), self.params['Validation batch size']['value'])
            try:
                # Worker in a separate thread
                self.thread = QThread()
                self.worker = AsyncWorker(self.train_and_test, (train_strategy, training_data,
                                                                test_strategy, test_data))
                self.worker.moveToThread(self.thread)

                self.thread.started.connect(self.worker.run)
                self.worker.finished.connect(self.cleanup_thread)
                self.worker.error.connect(self.error)

                self.thread.start()

            except Exception as e:
                self.error(str(e))

        self.train_btn.setEnabled(False)
        self.cancel_btn.setText('Close')

    def train_and_test(self, train_strategy: PytorchTraining, training_data: Dataset,
                       test_strategy: PytorchTesting, test_data: Dataset):
        """Procedure to execute in sequence training and testing"""
        self.nn = train_strategy.train(self.nn, training_data)
        self.is_nn_trained = True
        test_strategy.test(self.nn, test_data)

    def cleanup_thread(self):
        """Utility method to terminate threads correctly"""
        self.thread.quit()
        self.thread.wait()
        self.worker.deleteLater()
        self.thread.deleteLater()

    def error(self, msg: str = ''):
        """Display error message"""
        self.cleanup_thread()
        self.nn = None
        dialog = MessageDialog('Training error:\n' + msg, MessageType.ERROR)
        dialog.exec()
        self.close()


class VerificationWindow(BaseWindow):
    """
    This class is a Window for the verification of the network.
    It features a combo box for choosing the verification
    heuristic and a text render for the result

    Attributes
    ----------
    nn : SequentialNetwork
        The current network in the main window, already trained
    properties : dict
        Dictionary of properties to verify on the nn
    strategy : VerificationStrategy
        The verification class to use in the verification procedure
    params : dict
        Dictionary of parameters to load in the window

    Methods
    ----------
    execute_verification()
        Procedure to launch the verification.

    """

    def __init__(self, nn: SequentialNetwork, properties: dict):
        super().__init__('Verify network')

        self.nn = nn
        self.properties = properties
        self.strategy = None  # VerificationStrategy

        self.params = rep.read_json(RES_DIR + '/json/verification.json')

        # Content
        tab_layout = QHBoxLayout()

        self.verification_tabs = VerificationTabWidget(self.params)

        tab_layout.addWidget(self.verification_tabs)
        self.layout.addLayout(tab_layout)

        # Buttons
        btn_layout = QHBoxLayout()

        self.cancel_btn = CustomButton('Cancel')
        self.cancel_btn.clicked.connect(self.close)
        self.verify_btn = CustomButton('Verify network', primary=True)
        self.verify_btn.clicked.connect(self.set_and_launch_verification)

        btn_layout.addWidget(self.cancel_btn)
        btn_layout.addWidget(self.verify_btn)
        self.layout.addLayout(btn_layout)

        self.render_layout()

    def set_and_launch_verification(self) -> None:
        """
        This method launches the verification of the network
        based on the selection in the interface

        """

        # Set up verification property
        path = 'never2/' + self.__repr__().split(' ')[-1].replace('>', '') + '.smt2'
        file.write_smt_property(path, self.properties, 'Real')

        # Add logger dialog
        log_textbox = CustomLoggerTextArea(self)
        handler = CustomLoggingHandler()
        handler.log_signal.connect(log_textbox.appendPlainText)
        self.layout.addWidget(log_textbox)

        logger = logging.getLogger('pynever.strategies.verification')
        logger.setLevel(logging.INFO)
        logger.addHandler(handler)

        logger.info('***** NeVer 2 - VERIFICATION *****')

        # Load property from file
        to_verify = VnnLibProperty(path)
        # Property read, delete file
        os.remove(path)

        # Retrieve verification parameters
        strategy, raw_params = self.verification_tabs.get_params()
        match strategy:
            case 'SSLP':
                abst_logger = logging.getLogger('pynever.strategies.abstraction.layers')
                abst_logger.setLevel(logging.INFO)
                abst_logger.addHandler(handler)
                self.strategy = SSLPVerification(self.get_verification_params(strategy, raw_params))

            case 'SSBP':
                bp_logger = logging.getLogger("pynever.strategies.bounds_propagation")
                bp_logger.setLevel(logging.INFO)
                bp_logger.addHandler(handler)
                self.strategy = SSBPVerification(self.get_verification_params(strategy, raw_params))

            case _:
                raise NotImplementedError(f'The selected strategy {strategy} is not yet implemented')

        try:
            # Worker in a separate thread
            self.thread = QThread()
            self.worker = AsyncWorker(self.strategy.verify, (self.nn, to_verify))
            self.worker.moveToThread(self.thread)

            self.thread.started.connect(self.worker.run)
            self.worker.finished.connect(self.cleanup_thread)
            self.worker.error.connect(self.error)

            self.thread.start()

        except Exception as e:
            self.error(str(e))

        self.verify_btn.setEnabled(False)
        self.cancel_btn.setText('Close')

    def cleanup_thread(self):
        """Utility method to terminate threads correctly"""
        self.thread.quit()
        self.thread.wait()
        self.worker.deleteLater()
        self.thread.deleteLater()

    def error(self, msg: str = ''):
        """Display error message"""
        self.cleanup_thread()
        dialog = MessageDialog('Verification error:\n' + msg, MessageType.ERROR)
        dialog.exec()
        self.close()

    def get_verification_params(self, strategy: str, raw_params: dict[str, str]) \
            -> SSLPVerificationParameters | SSBPVerificationParameters:
        """
        This method translates the parameters read from the verification dialog
        to the corresponding VerificationParameters object.

        Parameters
        ----------
        strategy : str
            The name of the verification strategy
        raw_params : dict
            The dictionary of the dialog parameters

        Returns
        -------
        SSLPVerificationParameters | SSBPVerificationParameters

        """

        match strategy:
            case 'SSLP':

                match raw_params['heuristic']:
                    case 'Complete':
                        heuristic = 'complete'
                    case 'Approximate':
                        heuristic = 'overapprox'
                    case 'Mixed':
                        heuristic = 'mixed'
                    case _:
                        heuristic = 'complete'

                neurons = None

                if heuristic == 'mixed':
                    if ',' in raw_params['neurons_to_refine']:
                        neurons = [int(x) for x in raw_params['neurons_to_refine'].split(',')]
                    else:
                        neurons = int(raw_params['neurons_to_refine'])

                return SSLPVerificationParameters(heuristic, neurons)

            case 'SSBP':

                match raw_params['heuristic']:
                    case 'Sequential':
                        refinement = RefinementStrategy.SEQUENTIAL
                    case 'Lowest approximation':
                        refinement = RefinementStrategy.LOWEST_APPROX
                    case 'Lowest approximation in layer':
                        refinement = RefinementStrategy.LOWEST_APPROX_CURRENT_LAYER
                    case 'Input bounds change':
                        refinement = RefinementStrategy.INPUT_BOUNDS_CHANGE
                    case _:
                        refinement = RefinementStrategy.SEQUENTIAL

                match raw_params['bounds']:
                    case 'Symbolic':
                        bounds = BoundsBackend.SYMBOLIC
                    case _:
                        bounds = BoundsBackend.SYMBOLIC

                match raw_params['bounds_direction']:
                    case 'Forwards':
                        direction = BoundsDirection.FORWARDS
                    case 'Backwards':
                        direction = BoundsDirection.BACKWARDS
                    case _:
                        direction = BoundsDirection.FORWARDS

                match raw_params['intersection']:
                    case 'Star LP':
                        intersection = IntersectionStrategy.STAR_LP
                    case 'Adaptive':
                        intersection = IntersectionStrategy.ADAPTIVE
                    case _:
                        intersection = IntersectionStrategy.STAR_LP

                timeout = int(raw_params['timeout'])

                return SSBPVerificationParameters(refinement, bounds, direction, intersection, timeout)

            case _:
                raise NotImplementedError(f'The selected strategy {strategy} is not yet implemented')
