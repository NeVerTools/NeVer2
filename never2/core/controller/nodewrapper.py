from pynever.nodes import LayerNode, ReLUNode, FullyConnectedNode, BatchNormNode, \
    AveragePoolNode, ConvNode, MaxPoolNode, LRNNode, SoftMaxNode, UnsqueezeNode, FlattenNode, DropoutNode, \
    ReshapeNode, SigmoidNode


class NodeOps:
    @staticmethod
    def create_node(class_name: str, node_id: str, data: dict, in_dim: tuple) -> LayerNode:
        """
        This method builds the corresponding LayerNode given the
        class name, the unique identifier and the node data.
        If the class name is not part of the implemented set, an
        exception is raised.

        Parameters
        ----------
        class_name : str
            The name of the node type.
        node_id : str
            The unique identifier of the node.
        data : dict
            The dictionary containing the node data.
        in_dim : tuple
            The input of the node.

        Returns
        ----------
        LayerNode
            The concrete LayerNode object.

        """

        if class_name == 'ReLUNode':
            node = ReLUNode(node_id,
                            in_dim)
        elif class_name == 'SigmoidNode':
            node = SigmoidNode(node_id,
                               in_dim)
        elif class_name == 'FullyConnectedNode':
            node = FullyConnectedNode(node_id,
                                      in_dim,
                                      data["out_features"],
                                      weight=None, bias=None,
                                      has_bias=data["has_bias"])
        elif class_name == 'BatchNormNode':
            node = BatchNormNode(node_id,
                                 in_dim, weight=None,
                                 bias=None,
                                 running_mean=None,
                                 running_var=None, eps=data["eps"],
                                 momentum=data["momentum"], affine=data["affine"],
                                 track_running_stats=data["track_running_stats"])
        elif class_name == 'AveragePoolNode':
            node = AveragePoolNode(node_id,
                                   in_dim,
                                   data["kernel_size"],
                                   data["stride"],
                                   data["padding"],
                                   data["ceil_mode"],
                                   data["count_include_pad"])
        elif class_name == 'ConvNode':
            node = ConvNode(node_id,
                            in_dim,
                            data["out_channels"],
                            data["kernel_size"],
                            data["stride"],
                            data["padding"],
                            data["dilation"],
                            data["groups"],
                            data["has_bias"],
                            bias=None, weight=None)
        elif class_name == 'MaxPoolNode':
            node = MaxPoolNode(node_id,
                               in_dim,
                               data["kernel_size"],
                               data["stride"],
                               data["padding"],
                               data["dilation"],
                               data["ceil_mode"],
                               data["return_indices"])
        elif class_name == 'LRNNode':
            node = LRNNode(node_id,
                           in_dim,
                           data["size"],
                           data["alpha"],
                           data["beta"],
                           data["k"])
        elif class_name == 'SoftMaxNode':
            node = SoftMaxNode(node_id,
                               in_dim,
                               data["axis"])
        elif class_name == 'UnsqueezeNode':
            node = UnsqueezeNode(node_id,
                                 in_dim,
                                 data["axes"])
        elif class_name == 'FlattenNode':
            node = FlattenNode(node_id,
                               in_dim,
                               data["axis"])
        elif class_name == 'DropoutNode':
            node = DropoutNode(node_id,
                               in_dim,
                               data["p"])
        elif class_name == 'ReshapeNode':
            node = ReshapeNode(node_id,
                               in_dim,
                               data["shape"])
        else:
            raise Exception(class_name + " node not implemented")

        return node

    @staticmethod
    def update_node_input(node: LayerNode, in_dim: tuple) -> LayerNode:
        """
        This method updates the in_dim and out_dim parameters of
        the node passed.

        Parameters
        ----------
        node : LayerNode
            The node to update.
        in_dim : tuple
            The input shape.

        Returns
        ----------
        LayerNode
            The updated node.

        """

        # Abstract method executes the correct implementation
        node.update_input(in_dim)

        return node

    @staticmethod
    def update_node_data(node: LayerNode, data: dict) -> LayerNode:
        """
        This method updates the node data with the ones contained
        in the dictionary. For each parameter a number of controls
        is performed and the node is finally returned.

        Parameters
        ----------
        node : LayerNode
            The node to update.
        data : dict
            The new data to save.

        Returns
        ----------
        LayerNode
            The updated node.

        """

        if isinstance(node, FullyConnectedNode):
            node.out_features = data["out_features"]
            node.has_bias = data["has_bias"]
        elif isinstance(node, BatchNormNode):
            node.eps = data["eps"]
            node.momentum = data["momentum"]
            node.affine = data["affine"]
            node.track_running_stats = data["track_running_stats"]
        elif isinstance(node, ConvNode):
            node.out_channels = data["out_channels"]
            node.kernel_size = data["kernel_size"]
            node.stride = data["stride"]
            node.padding = data["padding"]
            node.dilation = data["dilation"]
            node.groups = data["groups"]
        elif isinstance(node, AveragePoolNode):
            node.kernel_size = data["kernel_size"]
            node.stride = data["stride"]
            node.padding = data["padding"]
            node.ceil_mode = data["ceil_mode"]
            node.count_include_pad = data["count_include_pad"]
        elif isinstance(node, MaxPoolNode):
            node.kernel_size = data["kernel_size"]
            node.stride = data["stride"]
            node.padding = data["padding"]
            node.dilation = data["dilation"]
            node.ceil_mode = data["ceil_mode"]
            node.return_indices = data["return_indices"]
        elif isinstance(node, LRNNode):
            node.size = data["size"]
            node.alpha = data["alpha"]
            node.beta = data["beta"]
            node.k = data["k"]
        elif isinstance(node, SoftMaxNode):
            node.axis = data["axis"]
        elif isinstance(node, UnsqueezeNode):
            node.axes = data["axes"]
        elif isinstance(node, ReshapeNode):
            node.shape = data["shape"]
            node.allow_zero = data["allow_zero"]
        elif isinstance(node, FlattenNode):
            node.axis = data["axis"]
        elif isinstance(node, DropoutNode):
            node.p = data["p"]

        return node

    @staticmethod
    def node2data(node: LayerNode) -> tuple:
        """
        This method creates a tuple with the information
        to draw a new block.

        Parameters
        ----------
        node : LayerNode
            The node to get data from.

        Returns
        ----------
        tuple
            The dictionary of the node data and the in_dim shape.

        """

        data = dict()

        if isinstance(node, FullyConnectedNode):
            data["in_features"] = node.in_features
            data["out_features"] = node.out_features
            data["weight"] = node.weight
            data["bias"] = node.bias
            data["has_bias"] = node.has_bias
        elif isinstance(node, BatchNormNode):
            data["num_features"] = node.num_features
            data["weight"] = node.weight
            data["bias"] = node.bias
            data["running_mean"] = node.running_mean
            data["running_var"] = node.running_var
            data["eps"] = node.eps
            data["momentum"] = node.momentum
            data["affine"] = node.affine
            data["track_running_stats"] = node.track_running_stats
        elif isinstance(node, AveragePoolNode):
            data["kernel_size"] = node.kernel_size
            data["stride"] = node.stride
            data["padding"] = node.padding
            data["ceil_mode"] = node.ceil_mode
            data["count_include_pad"] = node.count_include_pad
        elif isinstance(node, ConvNode):
            data["in_channels"] = node.in_channels
            data["out_channels"] = node.out_channels
            data["kernel_size"] = node.kernel_size
            data["stride"] = node.stride
            data["padding"] = node.padding
            data["dilation"] = node.dilation
            data["groups"] = node.groups
            data["has_bias"] = node.has_bias
            data["bias"] = node.bias
            data["weight"] = node.weight
        elif isinstance(node, MaxPoolNode):
            data["kernel_size"] = node.kernel_size
            data["stride"] = node.stride
            data["padding"] = node.padding
            data["dilation"] = node.dilation
            data["ceil_mode"] = node.ceil_mode
            data["return_indices"] = node.return_indices
        elif isinstance(node, LRNNode):
            data["size"] = node.size
            data["alpha"] = node.alpha
            data["beta"] = node.beta
            data["k"] = node.k
        elif isinstance(node, SoftMaxNode):
            data["axis"] = node.axis
        elif isinstance(node, UnsqueezeNode):
            data["axes"] = node.axes
        elif isinstance(node, FlattenNode):
            data["axis"] = node.axis
        elif isinstance(node, DropoutNode):
            data["p"] = node.p
        elif isinstance(node, ReshapeNode):
            data["shape"] = node.shape
            data["allow_zero"] = node.allow_zero

        return data, node.in_dim
