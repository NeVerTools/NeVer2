"""
Module project.py

This module contains the Project class for handling pynever's representation and I/O interfaces

Author: Andrea Gimelli, Giacomo Rosato, Stefano Demarchi

"""

from pynever.networks import SequentialNetwork, NeuralNetwork, AcyclicNetwork
from pynever.nodes import ConcreteLayerNode
from pynever import nodes
from pynever.exceptions import NotInNetworkError
import builtins

import never2.utils.rep as rep
from never2.utils.file import InputHandler, FileFormat, OutputHandler
from never2.utils.node_wrapper import NodeFactory
from never2.view.ui.dialogs.message import FuncDialog, YesNoDialog
from never2.view.ui.dialogs.dialog import InputDialog

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication, QFileDialog

def qt_string_input(prompt=''):
    """
    Replacement for built-in input() using a Qt dialog when expecting strings.
    """
    app = QApplication.instance()
    if app is None:
        app = QApplication([])

    # WARNING: we assume that the batch size is not specified
    dialog = InputDialog(message=prompt)
    if dialog.exec():
        return str(dialog.result)
    else:
        KeyboardInterrupt("Input cancelled")

def qt_yesno_input(prompt=''):
    """
    Replacement for built-in input() using a Qt dialog when expecting a yes/no choice.
    Returns 'y' for yes, 'n' for no.
    """
    app = QApplication.instance()
    if app is None:
        app = QApplication([])

    dialog = YesNoDialog(message=prompt)

    if dialog.exec():
        # Convert dialog result to 'y' or 'n'
        if dialog.result is True or dialog.result == "yes":
            return "y"
        else:
            return "n"
    else:
        raise KeyboardInterrupt("Input cancelled")

class Project:
    """
    This class serves as a manager for the definition of a pynever Neural Network object.
    It provides methods to update the network reflecting the actions in the graphical interface
    
    Attributes
    ----------
    scene_ref : Scene
        Reference to the scene
    nn : AcyclicNetwork
        The network object instantiated by the interface
    filename : (str, str)
        The filename of the network stored in a tuple (name, extension)
    
    """

    def __init__(self, scene: 'Scene', filename: str = None):
        # Reference to the scene
        self.scene_ref = scene

        # Default init is acyclic
        input_ids = self.scene_ref.input_block.get_identifier()
        self.nn = AcyclicNetwork('net', input_ids=input_ids)

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

    def get_input_ids_by_id(self, id:str) -> str:
        return [p for p in self.nn.get_input_ids_by_node(self.nn.nodes[id])] if id in self.nn.nodes else None 

    def get_parents_ids_by_id(self, id:str) -> str:
        return [p.identifier for p in self.nn.get_parents(self.nn.nodes[id])] if id in self.nn.nodes else None 

    def get_children_ids_by_id(self, id:str) -> str:
        return [p.identifier for p in self.nn.get_children(self.nn.nodes[id])] if id in self.nn.nodes else None 

    def have_single_output(self) -> bool:
        """
        Check if there is only one output in the network (nn). In particular looking at the number of nodes without children.
        Returns
        ----------
        bool
            True if there is only one node with no children, False otherwise.
            Note that if the newtork is empy False is returned. 
        """
        one_output_found = False
        for node in self.nn.nodes.values():
            if len(self.nn.get_children(node)) == 0:
                print(node)
                if one_output_found:
                    return False
                one_output_found = True
        return True
    
    def get_out_dim(self, id:str = None) -> tuple:
        """
        Compute and return the specified node's out_dim if the id has a corrispondence 
        with a node in the network, read from the input block otherwise.
        If no id is specified, the last block (if any) is considered.

        Parameters
        ----------
        id : str
            The id of the node to get the its out dimension
        Returns
        ----------
        tuple
            The output dimension of the node with specified id or the last one if id is None

        """

        if self.nn.is_empty() or id not in self.nn.nodes:
            return rep.text2tuple(self.scene_ref.input_block.content.wdg_param_dict['Dimension'][1])

        else:
            return self.nn.nodes[id].out_dim if id else self.nn.get_last_node().out_dim

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
                self.nn = AcyclicNetwork('net', new_input_id)

    def add_to_nn(self, layer_name: str, layer_id: str, data: dict, parents_ids:list[str] = None) -> ConcreteLayerNode:
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
        parents_ids:list[str]
            The list of ids of the parents (that must be in the network already)
        Returns
        ----------
        ConcreteLayerNode
            The node added to the network

        """
        layer_in_dim = tuple(self.get_out_dim(pid) for pid in parents_ids)
        if len(layer_in_dim) == 1:
            layer_in_dim = layer_in_dim[0]
        if len(layer_in_dim) == 0: # if no dimensions are found, it must be the input
            layer_in_dim = rep.text2tuple(self.scene_ref.input_block.content.wdg_param_dict['Dimension'][1])

        input_ids = None
        if len(parents_ids) == 0:#TODO: Horrible workaround
            parents_ids.append('INP')

        if 'INP' in parents_ids:
            input_ids = [self.nn.get_input_id()] #TODO: We assume only one input for the moment
            # parents_ids.remove('INP')
            # The removal is necessary beacuse the input is not in the
            # nodes of the internal representation, it must be handled in a sperate way
        
        parents = [self.nn.nodes[pid] for pid in parents_ids if pid != 'INP']
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
        if isinstance(self.nn, AcyclicNetwork):
            self.nn.add_node(node=new_node, parents=parents, input_ids=input_ids)
        self.set_modified(True)

        return new_node

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
        to_remove = self.nn.nodes.get(node_id) #get to not raise a keyvalue error if node_id is not a key
        parents_ids = self.get_parents_ids_by_id(node_id)
        self.modify_and_delete_node(node_id) #here an error is raised if the node is not in the network

        data = rep.format_data(params)

        #this may fail if parameters are illegal
        new_node = self.add_to_nn(str(to_remove.__class__.__name__), node_id, data, parents_ids)

        return new_node

    def modify_and_delete_node(self, id:str) -> ConcreteLayerNode:
        self.set_modified(True)
        if not id in self.nn.nodes:
            raise NotInNetworkError("Trying to remove a node that is not in the network")
        return self.nn.remove_node(self.nn.nodes[id])

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
            original_input = builtins.input
            builtins.input = lambda prompt='Please provide input dimension for the network:': qt_string_input(prompt)
            try:
                self.nn = handler.read_network(self.filename[0])
                
                if isinstance(self.nn, SequentialNetwork):
                    if self.nn.get_input_id() == '':
                        self.nn.input_ids = {'INP': self.nn.get_first_node().identifier}

                    self.nn = self.nn.to_acyclic_network() # generalize the conversion to acyclic TODO: Ask Andrea whether to use this or prune the sequential case
                
                # Display the network
                self.scene_ref.draw_network(self)

            finally:
                QApplication.restoreOverrideCursor()
                builtins.input = original_input

    def save(self, _as: bool = True) -> bool:
        """
        Convert the network and save to file

        """

        old_filename = self.filename  # Backup

        if self.nn.is_empty():
            raise Exception('The neural network is empty')
        
        if not self.have_single_output():
            raise Exception('The neural network must have a single output')

        if _as or self.filename == ('', ''):
            self.filename = QFileDialog.getSaveFileName(None, 'Save File', '', FileFormat.NETWORK_FORMATS_SAVE)

            if self.filename == ('', ''):
                self.filename = old_filename

        if self.filename != ('', ''):
            handler = OutputHandler()
            self.nn.identifier = self.filename[0].split('/')[-1].split('.')[0]

            QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)

            original_input = builtins.input
            builtins.input = lambda prompt='Do you want to save your PyTorch model as a traced model?': qt_yesno_input(prompt)

            try:
                handler.save(self.nn, self.filename)

                if self.scene_ref.has_properties():
                    handler.save_properties(self.scene_ref.get_properties(), self.filename)
            finally:
                 QApplication.restoreOverrideCursor()
                 builtins.input = original_input

            self.set_modified(False)

            return True

        return False
