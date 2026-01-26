"""
Module scene.py

This module contains the class Scene which is used as the manager of logic and graphics objects.

Author: Andrea Gimelli, Giacomo Rosato, Stefano Demarchi

"""

from never2.model.component.socket import SocketType
import torch
import numpy as np #TODO: this is necessary for the eval to work in some cases
from pynever.nodes import ConcreteLayerNode

import never2.utils.rep as rep
from never2.model.component.block import FunctionalBlock, Block, LayerBlock, PropertyBlock
from never2.model.component.edge import Edge
from never2.model.project import Project
from never2.resources.styling.custom import CustomLabel, CustomTextBox
from never2.utils.container import PropertyContainer
from never2.utils.node_wrapper import NodeFactory
from never2.view.graphics_scene import GraphicsScene
from never2.view.graphics_view import GraphicsView
from never2.view.ui.dialogs.message import ConfirmDialog, MessageDialog, MessageType

from PyQt6.QtGui import QGuiApplication
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QGraphicsItem

class Scene:
    """
    This class is the manager of logic and graphics objects. It has connections to the
    GraphicsScene class which handles the graphics objects, the GraphicsView class which
    renders them and the Project class which handles the pynever representation of the NN

    """

    def __init__(self, editor_widget: 'EditorWidget'):
        # Reference to the editor widget
        self.editor_widget_ref = editor_widget

        # Dictionary of the displayed blocks
        self.blocks = {}

        # Actual selected blocks
        self.selected_blocks_ids = []

        # Blocks counter
        self.blocks_count = 0

        # Graphics scene
        self.graphics_scene = GraphicsScene(self)
        
        # Connect to the signal emitted by PyQt6 on selection of new objects
        self.graphics_scene.selectionChanged.connect(self.update_selected_nodes)

        # Graphics view
        self.view = GraphicsView(self.graphics_scene)
        self.editor_widget_ref.splitter.addWidget(self.view)

        # Initialize I/O blocks
        self.input_block, self.output_block = self.init_io()

        # Input property block
        self.pre_block = None

        # Output property block
        self.post_block = None

        # Project with pynever NN object and interfaces
        self.project = Project(self)

    def init_io(self) -> tuple[FunctionalBlock, FunctionalBlock]:
        """
        This method creates the input and output blocks, which are permanent

        Returns
        ----------
        tuple
            Input block and Output block

        """

        input_block = FunctionalBlock(self, True)
        output_block = FunctionalBlock(self, False)

        # Add to blocks dict
        self.blocks[input_block.id] = input_block
        self.blocks[output_block.id] = output_block

        # Init start position in the view
        input_block.graphics_block.setPos(-300, -60)
        output_block.graphics_block.setPos(100, -60)

        self.blocks_count += 2

        return input_block, output_block

    def has_network(self) -> bool:
        return False if self.project is None else self.project.nn.is_empty()

    def has_properties(self) -> bool:
        return self.pre_block is not None or self.post_block is not None

    def get_properties(self) -> dict[str, PropertyContainer]:
        """
        Pack properties in a container and return

        """

        props = dict()

        if self.pre_block is not None:
            props[self.input_block.get_identifier()] = PropertyContainer(self.pre_block.smt_string,
                                                                         self.pre_block.variables,
                                                                         self.pre_block.title)

        if self.post_block is not None:
            props[self.output_block.get_identifier()] = PropertyContainer(self.post_block.smt_string,
                                                                          self.post_block.variables,
                                                                          self.post_block.title)

        return props

    def draw_network(self, project: Project) -> None:
        """
        Draw the opened network in the project

        """

        self.clear_scene()
        self.project = project

        in_dim = project.nn.get_first_node().get_input_dim() # TODO: this function assumes a single input
        if type(in_dim) == list: # if the first layer is a merge node, the dimension is a list (even if there is only one elment)
            in_dim = in_dim[0]
        self.input_block.set_identifier(project.nn.get_input_id())
        self.input_block.set_dimension(in_dim)

        #TODO: can we support more than one input (node) and more than one ouput in some way?
        nodes_to_add = project.nn.get_input_only_nodes() # can handle a branch at the beginning but not multiple inputs
        last_node = project.nn.get_last_node() # assumes a single output

        for node_to_add in nodes_to_add:
            parents_ids =  project.get_parents_ids_by_id(node_to_add.identifier)
            # Before creating the block, each parent of the node should be already drawed
            if all([parent_id in self.blocks.keys() for parent_id in parents_ids]): # if the node have all the parents drawn
                load_dict, node_id = NodeFactory.create_datanode(node_to_add)

                signature = str(load_dict['category']) + ':' + str(load_dict['name'])
                self.add_layer_block(self.editor_widget_ref.block_data[load_dict['category']][load_dict['name']],
                                        signature, node_id, load_dict, 
                                        parents_ids=parents_ids + project.get_input_ids_by_id(node_to_add.identifier))

                if not node_id == last_node.identifier:
                    children = project.nn.get_children(node_to_add)
                    for child in children: # we did not use sets to preserve the order of the queue
                        if child not in nodes_to_add:                      
                            nodes_to_add.append(child)

            else: # we postpone the creation of the block
                nodes_to_add.append(node_to_add)

    def load_properties(self, prop_dict: dict[str, PropertyContainer]) -> None:
        """
        Load existing properties from a dictionary <ID> : <PropertyContainer>

        """

        if len(prop_dict.keys()) <= 2:  # At most one pre-condition and one post-condition
            # This list is used to allow a custom input name and 'X' as the property name
            available_list = ['X', self.input_block.get_identifier(), self.output_block.get_identifier(),
                              self.project.nn.get_last_node().identifier]

            # Check variables compatibility
            for prop_id, prop_value in prop_dict.items():
                if prop_id not in available_list:
                    raise Exception('This property appears to be defined on another network!\n'
                                    f'Unknown variable: {prop_id}')

                if prop_id in [self.input_block.get_identifier(), 'X']:
                    if not prop_value.check_variables_size(self.input_block.get_dimension()):
                        raise Exception('The number of input variables is not consistent between\n'
                                        'the property and the network!')

                if prop_id in [self.output_block.get_identifier(), self.project.nn.get_last_node().identifier]:
                    if not prop_value.check_variables_size(self.output_block.get_dimension()):
                        raise Exception('The number of output variables is not consistent between\n'
                                        'the property and the network!')

            # Check output id
            if self.project.nn.get_last_node().identifier in prop_dict.keys():
                new_smt_string = prop_dict[self.project.nn.get_last_node().identifier].smt_string.replace(
                    self.project.nn.get_last_node().identifier, self.output_block.get_identifier())

                new_variable_list = []
                for variable in prop_dict[self.project.nn.get_last_node().identifier].variables:
                    new_variable_list.append(variable.replace(
                        self.project.nn.get_last_node().identifier, self.output_block.get_identifier()))

                prop_dict[self.output_block.get_identifier()] = PropertyContainer(new_smt_string, new_variable_list)
                prop_dict.pop(self.project.nn.get_last_node().identifier)

            # Add properties to the scene
            in_id = self.input_block.get_identifier()
            out_id = self.output_block.get_identifier()
            if in_id in prop_dict.keys():
                self.add_property_block('Generic SMT', self.input_block, prop_dict[in_id])
            else:
                self.add_property_block('Generic SMT', self.input_block, prop_dict['X'])

            if out_id in prop_dict.keys() or out_id == self.project.nn.get_last_node().identifier:
                self.add_property_block('Generic SMT', self.output_block, prop_dict[out_id])

    def add_layer_block(self, block_data: dict, block_sign: str,
                           block_id: str = None, load_dict: dict = None, parents_ids:list[str] = []) -> LayerBlock | None:
        """
        This method adds a layer block to the scene and draws it in the view.
        The method handles the addition of a new layer during execution (via GUI) or via optional parameters (e.g. load from a file).
        In the case of creation during execution, the parents of the added layer are those present in selected_blocks_ids.

        Parameters
        ----------
        block_data : dict
            Block info stored in dictionary
        block_sign : str
            Signature of the block
        block_id : str, Optional
            Identifier provided when reading a network file
        load_dict : dict, Optional
            Extra dictionary with values for loading from file

        Returns
        ----------
        LayerBlock | None
            Returns the LayerBlock object if created, None otherwise

        """

        # Check if there is an output property
        if self.post_block:
            dialog = ConfirmDialog('Confirmation required',
                                   'If you edit the network the output property will be removed\n'
                                   'Do you wish to proceed?')
            dialog.exec()

            if dialog.confirm:
                self.remove_out_prop()
            else:
                return None

        if len(parents_ids) > 1 and block_data["name"] != "ConcatNode" and block_data["name"] != "SumNode":
            dialog = MessageDialog("Only Merge Layers can have more than one input", MessageType.ERROR)
            dialog.exec()
            return None

        # Add the block
        added_block = LayerBlock(self, [1], [1], block_data, block_sign, block_id, load_dict)

        # Get the parents ids of only the layers (to update the internal representation)
        prev_layer_ids = parents_ids if len(parents_ids) > 0 else []

        # Update the internal representation adding the new node
        # Case 1: the network is loaded from file
        if load_dict is not None and block_id is not None:
            if hasattr(added_block.graphics_block, 'content'):
                added_node = self.project.nn.nodes[block_id]
                self.update_block_params(added_block, added_node)

        # Case 2: the network is built on the fly
        else:
            try:
                if added_block.content is not None:
                    added_node = self.project.add_to_nn(added_block.attr_dict['name'],
                                                        added_block.id,
                                                        rep.format_data(added_block.content.wdg_param_dict),
                                                        parents_ids=prev_layer_ids)
                    self.update_block_params(added_block, added_node)
                else:
                    self.project.add_to_nn(added_block.attr_dict['name'],
                                           added_block.id, {},
                                           parents_ids=prev_layer_ids)
            except Exception as e:
                dialog = MessageDialog(str(e), MessageType.ERROR)
                dialog.exec()

                self.remove_block(added_block, logic=False)
                return None
        
        self.blocks_count += 1

        # Add the block in the list and dictionary
        self.blocks[added_block.id] = added_block

        # Remove last edge
        last_block_socket = self.output_block.input_sockets[0]
        if last_block_socket.edge is not None:
            last_block_socket.edge.remove()

        # Resolve parent blocks, defaulting to the input block when missing
        prev_blocks = (
            [self.blocks.get(b_id, self.input_block) for b_id in parents_ids]
            if parents_ids else
            [self.input_block]
        )

        for prev_block in prev_blocks:
            self.add_edge(prev_block, added_block)

            # Toggle the parameter modification, at this point so that if the try-except above fail we have no problem during node removal
            if prev_block.has_parameters():
                prev_block.graphics_block.content.toggle_content_enabled(False)

        # Set position
        added_block.set_block_pos()

        self.update_edge_to_output()
        self.update_out_dim()

        self.update_edge_dim(added_block)
        
        self.view.centerOn(added_block.pos.x() + added_block.width / 2, added_block.pos.y() + added_block.height / 2)
        
        self.selected_blocks_ids = [added_block.id]

        # Update the graphics
        for b in self.blocks.values():
            b.graphics_block.setSelected(False)

        added_block.graphics_block.setSelected(True)

        return added_block
    
    def update_edge_to_output(self):
        # And if it is the only layer without children, then we can add the edge to the output
        last_block = None
        for block in self.blocks.values():
            if isinstance(block, FunctionalBlock):
                continue
            children_ids = self.project.get_children_ids_by_id(block.id)
            if len(children_ids) == 0:
                if last_block:
                    last_block = None
                    break
                else:
                    last_block = block
        
        if len(self.output_block.input_sockets) > 0 and self.output_block.input_sockets[0].edge:
            self.output_block.input_sockets[0].edge.remove()

        # add the edge only if it is the last node and has no siblings
        if last_block:
            self.add_edge(last_block, self.output_block)

    def add_property_block(self, name: str, parent: FunctionalBlock, prop_cnt: PropertyContainer = None) -> None:
        """
        This function defines a property given the input or output block

        Parameters
        ----------
        name : str
            The name of the property
        parent : FunctionalBlock
            The block to attach the property to
        prop_cnt : PropertyContainer
            The container object for property data

        """

        if len(self.blocks) > 2:  # Check there are layers in the network
            new_block = PropertyBlock(self, name, parent)

            # Check there are no properties already
            if parent.get_property_block() is not None:
                dialog = ConfirmDialog('Replace property',
                                       'There is a property already\nReplace it?')
                dialog.exec()

                if dialog.confirm:
                    if parent.title == 'Input':
                        self.remove_in_prop()
                    else:
                        self.remove_out_prop()
                else:
                    return

            if prop_cnt is None:
                has_edits = new_block.edit()
            else:
                has_edits = True
                new_block.smt_string = prop_cnt.smt_string
                new_block.variables = prop_cnt.variables

            if has_edits:
                new_block.draw()

                if parent.title == 'Input' and not self.pre_block:
                    self.pre_block = new_block
                elif parent.title == 'Output' and not self.post_block:
                    self.post_block = new_block
        else:
            dialog = MessageDialog('No network defined for adding a property', MessageType.ERROR)
            dialog.exec()

    def add_edge(self, prev: Block, cur: Block) -> Edge | None:
        """
        Add and draw the edge connecting two blocks

        Parameters
        ----------
        prev : Block
            The block from where the edge starts
        cur : Block
            The block where the edge ends

        """
        if len(prev.output_sockets) < 1 or prev.output_sockets[-1].edge: # note,if there is an empty socket it must be the first, otherewise we have an error
            prev.add_socket(SocketType.OUTPUT)

        if len(cur.input_sockets) < 1 or cur.input_sockets[-1].edge:
            cur.add_socket(SocketType.INPUT)

        return Edge(self, prev, cur) if self.blocks_count > 0 else None

    @staticmethod
    def update_block_params(added_block: LayerBlock, added_node: ConcreteLayerNode) -> None:
        """
        Display the correct parameters on the graphics block

        Parameters
        ----------
        added_block : LayerBlock
            The block displayed in the view
        added_node : ConcreteLayerNode
            The corresponding neural network node

        """

        if hasattr(added_block.content, 'wdg_param_dict'):
            for param_name, param_value in added_block.content.wdg_param_dict.items():
                q_wdg = param_value[0]
                if isinstance(q_wdg, CustomLabel):
                    if hasattr(added_node, param_name):
                        node_param = getattr(added_node, param_name)
                        if isinstance(node_param, torch.Tensor):
                            sh = tuple(node_param.shape)
                            q_wdg.setText(rep.tuple2text(sh))
                        else:
                            q_wdg.setText(str(node_param))
                elif isinstance(q_wdg, CustomTextBox):
                    if hasattr(added_node, param_name) and getattr(added_node, param_name) != eval(q_wdg.text()):
                        q_wdg.setText(rep.tuple2text(getattr(added_node, param_name), prod=False))

    def update_edges(self) -> None:
        """
        Add new edges and reposition after an update occurs

        """

        # Blocks to connect
        start_block = None
        end_block = None

        for _, block in self.blocks.items():
            if not block.has_input():
                end_block = block
            elif not block.has_output():
                start_block = block

        if start_block is not None and end_block is not None:
            if start_block is not self.input_block or end_block is not self.output_block:
                self.add_edge(start_block, end_block)

    def update_edge_dim(self, block: Block) -> None:
        """
        Display the output dimension of a block in the following edge

        """

        if block.has_input():
            prev_id = block.input_sockets[0].edge.start_skt.block_ref.id

            if prev_id != 'INP':
                prev_out_dim = self.project.nn.nodes[prev_id].get_output_dim()
                block.input_sockets[0].edge.update_label(rep.tuple2text(prev_out_dim))

    def update_out_dim(self) -> None:
        """
        Write the output dimension in the output block

        """

        last_id = self.output_block.previous()[0] if self.output_block.previous() else 'INP'
        dim_wdg = self.output_block.content.wdg_param_dict['Dimension'][0]

        if last_id == 'INP':
            dim_value = ''
        else:
            last_node = self.project.nn.get_last_node()
            dim_value = rep.tuple2text(last_node.out_dim, prod=False)

        dim_wdg.setText(dim_value)
        self.output_block.content.wdg_param_dict['Dimension'][1] = dim_value

    def remove_block(self, block: Block, logic: bool = False) -> None:
        """
        Remove a block both from the view and from the network

        Parameters
        ----------
        block : Block
            The block to delete
        logic : bool, Optional
            Flag for deleting the corresponding node in the network

        """

        # If the block is a property logic is forced to False
        if isinstance(block, PropertyBlock):
            logic = False

        elif self.post_block is not None:
            dialog = ConfirmDialog('Confirm required',
                                   'If you edit the network the output property will be removed\n'
                                   'Do you wish to proceed?')
            dialog.exec()

            if dialog.confirm:
                self.remove_out_prop()
            else:
                return  # Early stopping

        # Update the selected blocks with the children of the removed block
        associated_node = self.get_node_from_id(block.id)
        if associated_node:
            self.selected_blocks_ids = [p.identifier for p in self.project.nn.get_parents(associated_node)] 

        if not isinstance(block, FunctionalBlock):
            ref_id = block.id
            block.remove()

            if ref_id in self.blocks:
                self.blocks.pop(ref_id)
                self.blocks_count -= 1

                # Re-enable widgets in the previous block
                prev_blocks_ids = self.project.get_parents_ids_by_id(ref_id)

                if logic:
                    self.project.modify_and_delete_node(block.id)  

                #TODO: in prev_blocks you may have the same block twice, should it be a set?
                # if there are no previous blocks, it must be the first layer
                prev_blocks = [self.blocks[prev_block_id] for prev_block_id in prev_blocks_ids]
                if not prev_blocks:
                    prev_blocks = [self.input_block]   

                for prev_block in prev_blocks:
                    children_ids = self.project.get_children_ids_by_id(prev_block.id)
                    if children_ids is None:
                        #check INP
                        #TODO: can we store the list of children of each nodes in the class to avoid recomputing it each time?
                        #TODO: we get info about input children only graphically, refactor to put some logic here
                        if prev_block == self.input_block:
                            children_ids = []
                            for output_socket in self.input_block.output_sockets:
                                if output_socket.edge is not None:
                                    children_ids.append(output_socket.edge.end_skt.block_ref)
                        else:
                            raise ValueError("List of children is None")
                    
                    if len(children_ids) == 0 and prev_block.has_parameters():
                        prev_block.graphics_block.content.toggle_content_enabled(True)

            if self.pre_block is not None and ref_id == self.pre_block.id:
                self.pre_block = None
            if self.post_block is not None and ref_id == self.post_block.id:
                self.post_block = None
            
            # At the end check wheter should put the output arrow or not, 
            # note that this depends on the removal of node, so must be done after modify_and_delete_node
            self.update_edge_to_output()
            self.update_out_dim()

    def get_node_from_id(self, id:str) -> ConcreteLayerNode | None:
        return self.project.nn.nodes[id] if id in self.project.nn.nodes else None


    def remove_in_prop(self) -> None:
        if self.pre_block is not None:
            self.pre_block.remove()
            self.pre_block = None

    def remove_out_prop(self) -> None:
        if self.post_block is not None:
            self.post_block.remove()
            self.post_block = None

    def clear_scene(self) -> None:
        """
        Clear all graphics objects, dictionaries and re-init the I/O blocks

        """

        self.graphics_scene.clear()
        self.blocks = {}
        self.blocks_count = 0
        self.pre_block = None
        self.post_block = None
        self.input_block, self.output_block = self.init_io()

    def get_item_at(self, pos: 'QPointF') -> 'QGraphicsItem':
        return self.view.itemAt(pos)
    
    def update_selected_nodes(self):
        # Check if Ctrl is pressed globally
        ctrl_pressed = QGuiApplication.keyboardModifiers() & Qt.KeyboardModifier.ControlModifier

        # If Ctrl is NOT pressed, reset the selection
        if not ctrl_pressed:
            self.selected_blocks_ids = []

        # Then add all currently selected items
        x = self.graphics_scene.selectedItems()
        for item in x:
            if hasattr(item, 'block_ref'):
                if isinstance(item.block_ref, (LayerBlock, PropertyBlock)) or isinstance(item.block_ref, (FunctionalBlock)):
                    if item.block_ref.id not in self.selected_blocks_ids:
                        self.selected_blocks_ids.append(item.block_ref.id)
