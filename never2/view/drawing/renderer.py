import copy

from pynever.networks import SequentialNetwork

from never2.core.controller.nodewrapper import NodeOps
from never2.view.drawing.element import NodeBlock, PropertyBlock


class SequentialNetworkRenderer:
    """
    This class is an attribute of the Canvas object: reading the Project
    attribute it builds a list of graphic NodeBlock objects composing the
    graph and changes it according to user events.

    Attributes
    ----------
    NN : SequentialNetwork
        Internal representation of the network.
    disconnected_network : dict
        Dictionary containing the network blocks.
    properties : dict
        Dictionary containing the network properties.
    available_blocks : dict
        Dictionary containing the set of the drawable blocks.

    Methods
    ----------
    is_nn_sequential(bool)
        Procedure to check whether the network is sequential.
    add_node_to_nn(str)
        Procedure to add a single disconnected node.
    add_disconnected_block(NodeBlock)
        Procedure to insert a new block in the disconnected set.
    add_edge(str, str)
        Procedure to add a new edge between two nodes.
    count_edges()
        Procedure to count the number of edges in the network.
    has_nodes_before(str)
        Procedure to check whether the node has nodes connected before it.
    delete_edge(str)
        Procedure to delete a given edge from the network.
    insert_node(str, str)
        explained below
    edit_node(str, dict)
        Procedure to edit the node attributes.
    delete_node(str)
        Procedure to delete the given node.
    update_network_from(str, str)
        explained below
    render(NeuralNetwork)
        explained below

    """

    def __init__(self, NN: SequentialNetwork, json_blocks: dict):
        self.NN = NN
        self.available_blocks = json_blocks
        self.disconnected_network = dict()
        self.properties = dict()

    def is_nn_sequential(self) -> bool:
        """
        This method checks whether the network is sequential.

        Returns
        ----------
        bool
            True if the network is sequential, False otherwise.

        """

        if len(self.disconnected_network) == 1:
            # If there is only one node, the network is sequential
            return True
        else:  # TODO rewrite with for loop?
            # Each node must be connected to the next with only one edge.
            n = self.NN.get_first_node().identifier
            count = 1
            while len(self.NN.edges[n]) == 1:
                n = self.NN.get_next_node(self.NN.nodes[n]).identifier
                count += 1
            # If one node has one or more edges, the network is not sequential
            if len(self.NN.edges[n]) > 1:
                return False
            # Finally, the count of nodes should equal the nodes in the network.
            return count == len(self.NN.nodes)

    def add_node_to_nn(self, node_id: str) -> None:
        """
        This method adds the given node to the project network,
        without connecting it.

        Parameters
        ----------
        node_id: str
            The node identifier.

        """

        try:
            if node_id in self.disconnected_network:
                block = self.disconnected_network[node_id]
                node = NodeOps.create_node(block.node.class_name, node_id,
                                           block.block_data, block.in_dim)
                self.NN.nodes[node_id] = node
                self.NN.edges[node_id] = []
        except Exception as e:
            raise e

    def add_disconnected_block(self, block: NodeBlock) -> None:
        """
        This method creates a new entry in the disconnected
        network with the given block.

        Parameters
        ----------
        block: NodeBlock
            The block to add in the disconnected network.

        """

        self.disconnected_network[block.block_id] = block

    def add_property_block(self, block: PropertyBlock) -> None:
        """
        This method creates a new entry in the properties
        dictionary with the given block.

        Parameters
        ----------
        block: PropertyBlock
            The block to add in the dictionary.

        """

        self.properties[block.block_id] = block

    def add_edge(self, origin_id: str, destination_id: str) -> bool:
        """
        This method adds a connection between two nodes, provided that
        the network remains sequential.

        Parameters
        ----------
        origin_id: str
            The identifier of the first node.
        destination_id: str
            The identifier of the second node.

        Returns
        ----------
        bool
            True if the insertion took place and the network is still
            sequential, False otherwise.

        """

        origin_block = self.disconnected_network[origin_id]
        destination_block = self.disconnected_network[destination_id]

        # If there are no nodes the origin becomes the first node and the second is added
        if not self.NN.nodes:
            st_node = NodeOps.create_node(origin_block.node.class_name,
                                          origin_block.block_id,
                                          origin_block.block_data,
                                          origin_block.in_dim)
            nd_node = NodeOps.create_node(destination_block.node.class_name,
                                          destination_block.block_id,
                                          destination_block.block_data,
                                          st_node.out_dim)
            self.NN.add_node(st_node)
            self.NN.add_node(nd_node)

            self.disconnected_network[nd_node.identifier].block_data = NodeOps.node2data(nd_node)[0]
            self.disconnected_network[nd_node.identifier].in_dim = nd_node.in_dim
            self.disconnected_network[nd_node.identifier].update_labels()

            return True

        # If the network is not empty but the nodes are not present they are created.
        # N.B. the network may become non sequential.
        elif origin_id not in self.NN.nodes and destination_id not in self.NN.nodes:
            st_node = NodeOps.create_node(origin_block.node.class_name,
                                          origin_block.block_id,
                                          origin_block.block_data,
                                          origin_block.in_dim)
            nd_node = NodeOps.create_node(destination_block.node.class_name,
                                          destination_block.block_id,
                                          destination_block.block_data,
                                          st_node.out_dim)

            self.NN.nodes[origin_id] = st_node
            self.NN.nodes[destination_id] = nd_node
            self.NN.edges[origin_id] = [destination_id]
            self.NN.edges[destination_id] = []

            self.disconnected_network[nd_node.identifier].block_data = NodeOps.node2data(nd_node)[0]
            self.disconnected_network[nd_node.identifier].in_dim = nd_node.in_dim
            self.disconnected_network[nd_node.identifier].update_labels()

            return True

        # If the nodes are all connected but one and the node are present the network
        # would be a loop, which is illegal.
        elif len(self.NN.nodes) == self.count_edges() + 1 and \
                origin_id in self.NN.nodes and \
                destination_id in self.NN.nodes:

            return False

        # If the origin has no connections after or the destination has no connections before
        # try to draw the new connection.
        elif (origin_id not in self.NN.nodes or len(self.NN.edges[origin_id]) == 0) and \
                not self.has_nodes_before(destination_id):
            if origin_id not in self.NN.nodes:
                orig_node = NodeOps.create_node(origin_block.node.class_name,
                                                origin_block.block_id,
                                                origin_block.block_data,
                                                origin_block.in_dim)
                self.NN.nodes[origin_id] = orig_node
                self.NN.edges[origin_id] = []
            else:
                orig_node = self.NN.nodes[origin_id]

            if destination_id not in self.NN.nodes:
                dest_node = NodeOps.create_node(destination_block.node.class_name,
                                                destination_block.block_id,
                                                destination_block.block_data,
                                                orig_node.out_dim)
                self.NN.nodes[destination_id] = dest_node
                self.NN.edges[destination_id] = []
            else:
                dest_node = self.NN.nodes[destination_id]
                NodeOps.update_node_input(dest_node, orig_node.out_dim)

                # Update blocks after
                if len(self.NN.edges[destination_id]) > 0:
                    self.update_network_from(destination_id, origin_id)

            self.NN.edges[origin_id].append(destination_id)
            self.disconnected_network[dest_node.identifier].block_data = NodeOps.node2data(dest_node)[0]
            self.disconnected_network[dest_node.identifier].in_dim = dest_node.in_dim
            self.disconnected_network[dest_node.identifier].update_labels()
            return True

        # The network is not Sequential
        else:
            return False

    def count_edges(self) -> int:
        """
        This method returns the number of edges in the network.

        Returns
        ----------
        int
            The count of the network edges.

        """

        edges = 0
        for edge_list in self.NN.edges.values():
            edges += len(edge_list)
        return edges

    def has_nodes_before(self, block_id: str) -> bool:
        """
        This method checks whether the given node is the destination
        of another node before.

        Parameters
        ----------
        block_id: str
            The identifier of the node.

        Returns
        ----------
        bool
            True if the node has nodes before, False otherwise.

        """

        for dest in self.NN.edges.values():
            if block_id in dest:
                return True
        return False

    def delete_edge_from(self, block_id: str):
        """
        This method deletes the outgoing edge from the
        given node.

        Parameters
        ----------
        block_id: str
            The identifier of the node.

        """

        self.NN.edges[block_id] = []

    def insert_node(self, cur_node_id: str, prev_node_id: str) -> bool:
        """
        This method inserts the node specified by cur_node_id
        right after the node specified by prev_node_id.

        Parameters
        ----------
        cur_node_id: str
            The identifier of the node to insert.
        prev_node_id: str
            The identifier of the previous node.

        Returns
        ----------
        bool
            True if the insert succeeded, False otherwise.

        """

        if prev_node_id == cur_node_id or \
                cur_node_id not in self.NN.nodes.keys() or \
                prev_node_id not in self.NN.nodes.keys():
            return False
        else:
            try:
                prev_node = self.NN.nodes[prev_node_id]
                middle_node_block = self.disconnected_network[cur_node_id]

                middle_node = NodeOps.create_node(middle_node_block.node.class_name,
                                                  middle_node_block.block_id,
                                                  middle_node_block.block_data,
                                                  in_dim=prev_node.out_dim)

                next_node = self.NN.get_next_node(prev_node)

                # Adjust the network
                self.NN.edges[prev_node_id] = []
                self.NN.edges[prev_node_id].append(middle_node.identifier)
                self.NN.edges[cur_node_id] = []
                self.NN.edges[cur_node_id].append(next_node.identifier)
                self.NN.nodes[cur_node_id] = middle_node

                # Update the network
                self.update_network_from(next_node.identifier,
                                         middle_node.identifier)
                return True

            except Exception as e:
                raise Exception(e)

    def edit_node(self, block_id: str, data: dict) -> bool:
        """
        This method updates the given node, editing the parameters given by
        the dictionary.

        Parameters
        ----------
        block_id: str
            The identifier of the node to edit.
        data: dict
            The dictionary containing the node data.

        Returns
        ----------
        bool
            True if the update has been done correctly, False otherwise.

        """

        in_dim = None
        out_dim = None

        if "in_dim" in data.keys():
            in_dim = data["in_dim"]
            data.pop("in_dim")

        if "out_dim" in data.keys():
            out_dim = data["out_dim"]
            data.pop("out_dim")

        # Copy current data
        old_data = copy.deepcopy(self.disconnected_network[block_id].block_data)
        old_in_dim = copy.deepcopy(self.disconnected_network[block_id].in_dim)

        # Update with new data
        for key, value in data.items():
            self.disconnected_network[block_id].block_data[key] = value
        data = self.disconnected_network[block_id].block_data

        if in_dim is not None:
            self.disconnected_network[block_id].in_dim = in_dim
        if out_dim is not None:
            self.disconnected_network[block_id].out_dim = out_dim

        if block_id not in self.NN.nodes.keys():
            return False

        node = self.NN.nodes[block_id]

        try:
            if in_dim is not None:
                NodeOps.update_node_input(node, in_dim)
            if out_dim is not None:
                node.out_dim = out_dim

            NodeOps.update_node_data(node, data)

            if node is not self.NN.get_last_node():
                next_node = self.NN.get_next_node(node)
                self.update_network_from(next_node.identifier, node.identifier)

            return True

        except Exception as e:
            # Restore block
            self.disconnected_network[block_id].block_data = old_data
            self.disconnected_network[block_id].in_dim = old_in_dim

            # Restore network
            NodeOps.update_node_data(node, old_data)
            if in_dim is not None:
                NodeOps.update_node_input(node, old_in_dim)

            if node is not self.NN.get_last_node():
                next_node = self.NN.get_next_node(node)
                self.update_network_from(next_node.identifier, node.identifier)

            raise Exception(str(e))

    def delete_node(self, block_id: str) -> tuple:
        """
        This method deletes a node, eventually recreating edges
        in order to keep the network connected.

        Parameters
        ----------
        block_id: str
            The identifier of the node to delete.

        Returns
        ----------
        tuple
            The new edge to draw when the node is deleted.

        """

        new_edge = None
        if block_id in self.NN.nodes:
            # Unroll the sequential network and find the previous node
            for k, node in self.NN.nodes.items():
                # If the node to remove isn't the last add the next node to the edges of the previous node
                if block_id in self.NN.edges[k]:
                    if block_id != self.NN.get_last_node().identifier:
                        next_node_id = self.NN.get_next_node(self.NN.nodes[block_id]) \
                            .identifier

                        try:
                            # Update network
                            self.update_network_from(next_node_id, k)

                            # Remove the edge between the previous node and the one to delete
                            self.NN.edges[k].remove(block_id)
                            self.NN.edges[k].append(next_node_id)
                            new_edge = (k, next_node_id)
                        except Exception as e:
                            raise Exception(e)
                    else:
                        # If the node is the last node
                        self.NN.edges[k].remove(block_id)
                    break

            # Delete the LayerNode and return the new edge to draw
            self.NN.nodes.pop(block_id)
            self.NN.edges.pop(block_id)

            if len(self.NN.nodes) == 1:
                only_node = self.NN.get_first_node().identifier
                self.NN.nodes.pop(only_node)
                self.NN.edges.pop(only_node)

        # Remove the block from the disconnected graph
        if block_id in self.disconnected_network:
            self.disconnected_network.pop(block_id)

        return new_edge

    def update_network_from(self, node_id: str, prev_node_id: str) -> None:
        """
        This method updates the dimensions of the network starting from
        the given node, assigning as the new input dimensions the output
        dimensions of the given previous node.

        Parameters
        ----------
        node_id: str
            The identifier of the node to update the network from.
        prev_node_id: str
            The identifier of the previous node.

        """

        node = self.NN.nodes[node_id]
        in_dim = self.NN.nodes[prev_node_id].out_dim

        if node is not None:
            while node is not None:
                NodeOps.update_node_input(node, in_dim)

                self.disconnected_network[node.identifier].block_data = NodeOps.node2data(node)[0]
                self.disconnected_network[node.identifier].in_dim = in_dim
                self.disconnected_network[node.identifier].update_labels()

                in_dim = node.out_dim
                node = self.NN.get_next_node(node)

    def render(self) -> tuple:
        """
        This method builds the graphic network to draw,
        composed of the nodes in the disconnected network
        and the edges computed.

        Parameters
        ----------

        Returns
        ----------
        tuple
            A tuple with the disconnected network dictionary and
            the list of edges.

        """

        # Fresh init
        self.disconnected_network = {}
        edges = list()

        for node in self.NN.nodes.values():
            for b in self.available_blocks.values():
                if b.class_name == node.__class__.__name__:
                    # Create the graphic block
                    block = NodeBlock(node.identifier, b)
                    block_data = NodeOps.node2data(node)
                    block.block_data = block_data[0]
                    block.in_dim = block_data[1]

                    self.disconnected_network[node.identifier] = block

        # Fetch connections
        for node, destination in self.NN.edges.items():
            if len(destination) > 0:
                edges.append((node, destination[0]))

        return self.disconnected_network, edges
