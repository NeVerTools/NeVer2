"""
Module project.py

This module contains the Project class for handling pynever's representation and I/O interfaces

Author: Andrea Gimelli, Giacomo Rosato, Stefano Demarchi

"""

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication, QFileDialog
from pynever.networks import SequentialNetwork
from pynever.nodes import ConcreteLayerNode

import never2.utils.rep as rep
from never2.utils.file import InputHandler, FileFormat, OutputHandler
from never2.utils.node_wrapper import NodeFactory
from never2.view.ui.dialogs.message import FuncDialog


class Project:
    """
    This class serves as a manager for the definition of a pynever Neural Network object.
    It provides methods to update the network reflecting the actions in the graphical interface
    
    Attributes
    ----------
    scene_ref : Scene
        Reference to the scene
    nn : SequentialNetwork
        The network object instantiated by the interface
    filename : (str, str)
        The filename of the network stored in a tuple (name, extension)
    
    """

    def __init__(self, scene: 'Scene', filename: str = None):
        # Reference to the scene
        self.scene_ref = scene

        # Default init is sequential, future extensions should either consider multiple initialization or
        # on-the-fly switch between Sequential and ResNet etc.
        self.nn = SequentialNetwork('net', self.scene_ref.input_block.get_identifier())

        self.set_modified(False)

        # File name is stored as a tuple (name, extension)
        if filename is not None:
            self.filename = filename
            self.open()

        else:
            self.filename = ('', '')

    def is_modified(self) -> bool:
        return self.scene_ref.editor_widget_ref.main_wnd_ref.isWindowModified() and self.nn.nodes

    def set_modified(self, value: bool) -> None:
        self.scene_ref.editor_widget_ref.main_wnd_ref.setWindowModified(value)

    def get_last_out_dim(self) -> tuple:
        """
        Compute and return the last node out_dim if there are nodes already,
        read from the input block otherwise

        Returns
        ----------
        tuple
            The last output dimension

        """

        if self.nn.is_empty():
            return rep.text2tuple(self.scene_ref.input_block.content.wdg_param_dict['Dimension'][1])

        else:
            return self.nn.get_last_node().out_dim

    def reset_nn(self, new_input_id: str, caller_id: str) -> None:
        """
        If a functional block is updated, the network is re-initialized

        Parameters
        ----------
        new_input_id : str
            New identifier for the network input
        caller_id : str
            The block that was updated (either 'INP' or 'END')

        """

        if caller_id == 'INP':
            if new_input_id not in self.nn.input_ids:
                self.nn = SequentialNetwork('net', new_input_id)

    def add_to_nn(self, layer_name: str, layer_id: str, data: dict) -> ConcreteLayerNode:
        """
        This method creates the corresponding layer node to the graphical block
        and updates the network

        Parameters
        ----------
        layer_name : str
            The ConcreteLayerNode name
        layer_id : str
            The id to assign to the new node
        data : dict
            The parameters of the node

        Returns
        ----------
        ConcreteLayerNode
            The node added to the network

        """

        layer_in_dim = self.get_last_out_dim()

        # Due to the multidimensional nature of some nodes, some hard-coded processing
        # in order to assign the correct value is needed.
        # TODO find a better workaround?

        kernel_dim = len(layer_in_dim) - 1
        padding_dim = 2 * kernel_dim

        if layer_name == 'ConvNode' or layer_name == 'AveragePoolNode' or layer_name == 'MaxPoolNode':
            data['kernel_size'] = tuple((data['kernel_size'][0] for _ in range(kernel_dim)))
            data['stride'] = tuple((data['stride'][0] for _ in range(kernel_dim)))
            data['padding'] = tuple((data['padding'][0] for _ in range(padding_dim)))

        if layer_name == 'ConvNode' or layer_name == 'MaxPoolNode':
            data['dilation'] = tuple((data['dilation'][0] for _ in range(kernel_dim)))

        new_node = NodeFactory.create_layernode(layer_name, layer_id, data, layer_in_dim)
        self.nn.append_node(new_node)
        self.set_modified(True)

        return new_node

    def link_to_nn(self, node: ConcreteLayerNode) -> None:
        """
        Alternative method for adding a layer directly

        Parameters
        ----------
        node : ConcreteLayerNode
            The node to add directly

        """

        self.nn.append_node(node)
        self.set_modified(True)

    def refresh_node(self, node_id: str, params: dict) -> None:
        """
        This method propagates the visual modifications to the logic node
        by deleting and re-adding it to the network

        Parameters
        ----------
        node_id : str
            The id key to the nodes dictionary
        params : dict
            The node parameters

        """

        # Delete and re-create the node
        to_remove = self.nn.nodes[node_id]
        self.delete_last_node()

        data = rep.format_data(params)
        new_node = self.add_to_nn(str(to_remove.__class__.__name__), node_id, data)

        # Update dimensions
        dim_wdg = self.scene_ref.output_block.content.wdg_param_dict['Dimension'][0]
        dim_wdg.setText(str(new_node.get_output_dim()))
        self.scene_ref.output_block.content.wdg_param_dict['Dimension'][1] = new_node.out_dim

    def delete_last_node(self) -> ConcreteLayerNode:
        self.set_modified(True)

        return self.nn.delete_last_node()

    def open(self) -> None:
        """
        Load a network from file and convert it in the internal representation

        """

        if not self.nn.is_empty() and self.is_modified():
            dialog = FuncDialog('Do you want to save your work?', self.save)
            dialog.exec()

        if self.filename != ('', ''):
            handler = InputHandler()

            QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
            self.nn = handler.read_network(self.filename[0])

            if isinstance(self.nn, SequentialNetwork) and self.nn.get_input_id() == '':
                self.nn.input_ids = {'X': self.nn.get_first_node().identifier}

            QApplication.restoreOverrideCursor()

            # Display the network
            self.scene_ref.draw_network(self)

    def save(self, _as: bool = True) -> bool:
        """
        Convert the network and save to file

        """

        old_filename = self.filename  # Backup

        if self.nn.is_empty():
            raise Exception('The neural network is empty')

        if _as or self.filename == ('', ''):
            self.filename = QFileDialog.getSaveFileName(None, 'Save File', '', FileFormat.NETWORK_FORMATS_SAVE)

            if self.filename == ('', ''):
                self.filename = old_filename

        if self.filename != ('', ''):
            handler = OutputHandler()
            self.nn.identifier = self.filename[0].split('/')[-1].split('.')[0]

            QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
            handler.save(self.nn, self.filename)

            if self.scene_ref.has_properties():
                handler.save_properties(self.scene_ref.get_properties(), self.filename)

            QApplication.restoreOverrideCursor()

            self.set_modified(False)

            return True

        return False
