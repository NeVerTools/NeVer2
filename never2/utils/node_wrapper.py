"""
Module node_wrapper.py

This module contains the factory class for instantiating nodes in pynever and dictionary formats

Author: Andrea Gimelli, Giacomo Rosato, Stefano Demarchi

"""

from pynever.nodes import LayerNode, ReLUNode, SigmoidNode, FullyConnectedNode, BatchNormNode, AveragePoolNode, \
    ConvNode, MaxPoolNode, LRNNode, SoftMaxNode, UnsqueezeNode, FlattenNode, DropoutNode, ReshapeNode, ELUNode, \
    CELUNode, LeakyReLUNode, TanhNode


class NodeFactory:
    """
    This class is a factory of node objects, both in the pynever representation and the
    dictionary one.

    Methods
    ----------
    create_layernode(str, str, dict, tuple)
        Procedure to build a pynever layer given the data

    create_datanode(LayerNode)
        Procedure to build a dict with the node data

    """

    @staticmethod
    def create_layernode(class_name: str, node_id: str, data: dict, in_dim: tuple) -> LayerNode:
        """
        This method builds the corresponding LayerNode given the class name,
        a unique identifier and the node data. If the class name is not implemented,
        raises an Exception

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
        elif class_name == 'ELUNode':
            node = ELUNode(node_id,
                           in_dim,
                           alpha=data['alpha'])
        elif class_name == 'CELUNode':
            node = CELUNode(node_id,
                            in_dim,
                            alpha=data['alpha'])
        elif class_name == 'LeakyReLUNode':
            node = LeakyReLUNode(node_id,
                                 in_dim,
                                 negative_slope=data['negative_slope'])
        elif class_name == 'SigmoidNode':
            node = SigmoidNode(node_id,
                               in_dim)
        elif class_name == 'TanhNode':
            node = TanhNode(node_id,
                            in_dim)
        elif class_name == 'FullyConnectedNode':
            node = FullyConnectedNode(node_id,
                                      in_dim,
                                      data['out_features'],
                                      weight=None, bias=None,
                                      has_bias=data['has_bias'])
        elif class_name == 'BatchNormNode':
            node = BatchNormNode(node_id,
                                 in_dim, weight=None,
                                 bias=None,
                                 running_mean=None,
                                 running_var=None, eps=data['eps'],
                                 momentum=data['momentum'], affine=data['affine'],
                                 track_running_stats=data['track_running_stats'])
        elif class_name == 'AveragePoolNode':
            node = AveragePoolNode(node_id,
                                   in_dim,
                                   data['kernel_size'],
                                   data['stride'],
                                   data['padding'],
                                   data['ceil_mode'],
                                   data['count_include_pad'])
        elif class_name == 'ConvNode':
            node = ConvNode(node_id,
                            in_dim,
                            data['out_channels'],
                            data['kernel_size'],
                            data['stride'],
                            data['padding'],
                            data['dilation'],
                            data['groups'],
                            data['has_bias'],
                            bias=None, weight=None)
        elif class_name == 'MaxPoolNode':
            node = MaxPoolNode(node_id,
                               in_dim,
                               data['kernel_size'],
                               data['stride'],
                               data['padding'],
                               data['dilation'],
                               data['ceil_mode'],
                               data['return_indices'])
        elif class_name == 'LRNNode':
            node = LRNNode(node_id,
                           in_dim,
                           data['size'],
                           data['alpha'],
                           data['beta'],
                           data['k'])
        elif class_name == 'SoftMaxNode':
            node = SoftMaxNode(node_id,
                               in_dim,
                               data['axis'])
        elif class_name == 'UnsqueezeNode':
            node = UnsqueezeNode(node_id,
                                 in_dim,
                                 data['axes'])
        elif class_name == 'FlattenNode':
            node = FlattenNode(node_id,
                               in_dim,
                               data['axis'])
        elif class_name == 'DropoutNode':
            node = DropoutNode(node_id,
                               in_dim,
                               data['p'])
        elif class_name == 'ReshapeNode':
            node = ReshapeNode(node_id,
                               in_dim,
                               data['shape'])
        else:
            raise Exception(class_name + ' node not implemented')

        return node

    @staticmethod
    def create_datanode(node: LayerNode) -> tuple:
        """
        This method creates a tuple with the information
        to draw a new block.

        Parameters
        ----------
        node : LayerNode
            The node to get data from.

        Returns
        ----------
        data
            The dictionary of the node data and the in_dim shape.

        node_identifier
            The id of the node

        """

        data = dict()

        if isinstance(node, ReLUNode):
            data['name'] = 'ReLU'
            data['category'] = 'Activation layers'
            data['parameters'] = dict()
        elif isinstance(node, ELUNode):
            data['name'] = 'ELU'
            data['category'] = 'Activation layers'
            data['parameters'] = dict()
            data['parameters']['alpha'] = node.alpha
        elif isinstance(node, CELUNode):
            data['name'] = 'CELU'
            data['category'] = 'Activation layers'
            data['parameters'] = dict()
            data['parameters']['alpha'] = node.alpha
        elif isinstance(node, LeakyReLUNode):
            data['name'] = 'Leaky ReLU'
            data['category'] = 'Activation layers'
            data['parameters'] = dict()
            data['parameters']['negative_slope'] = node.negative_slope
        elif isinstance(node, SigmoidNode):
            data['name'] = 'Sigmoid'
            data['category'] = 'Activation layers'
            data['parameters'] = dict()
        elif isinstance(node, TanhNode):
            data['name'] = 'Tanh'
            data['category'] = 'Activation layers'
            data['parameters'] = dict()
        elif isinstance(node, SoftMaxNode):
            data['name'] = 'SoftMax'
            data['category'] = 'Activation layers'
            data['parameters'] = dict()
            data['parameters']['axis'] = node.axis
        elif isinstance(node, FullyConnectedNode):
            data['name'] = 'Fully Connected'
            data['category'] = 'Linear layers'
            data['parameters'] = dict()
            data['parameters']['in_features'] = node.in_features
            data['parameters']['out_features'] = node.out_features
            data['parameters']['weight'] = node.weight
            data['parameters']['bias'] = node.bias
            data['parameters']['has_bias'] = node.has_bias
        elif isinstance(node, ConvNode):
            data['name'] = 'Convolutional'
            data['category'] = 'Convolution layers'
            data['parameters'] = dict()
            data['parameters']['in_channels'] = node.in_channels
            data['parameters']['out_channels'] = node.out_channels
            data['parameters']['kernel_size'] = node.kernel_size
            data['parameters']['stride'] = node.stride
            data['parameters']['padding'] = node.padding
            data['parameters']['dilation'] = node.dilation
            data['parameters']['groups'] = node.groups
            data['parameters']['has_bias'] = node.has_bias
            data['parameters']['bias'] = node.bias
            data['parameters']['weight'] = node.weight
        elif isinstance(node, AveragePoolNode):
            data['name'] = 'AveragePool'
            data['category'] = 'Pooling layers'
            data['parameters'] = dict()
            data['parameters']['kernel_size'] = node.kernel_size
            data['parameters']['stride'] = node.stride
            data['parameters']['padding'] = node.padding
            data['parameters']['ceil_mode'] = node.ceil_mode
            data['parameters']['count_include_pad'] = node.count_include_pad
        elif isinstance(node, MaxPoolNode):
            data['name'] = 'MaxPool'
            data['category'] = 'Pooling layers'
            data['parameters'] = dict()
            data['parameters']['kernel_size'] = node.kernel_size
            data['parameters']['stride'] = node.stride
            data['parameters']['padding'] = node.padding
            data['parameters']['dilation'] = node.dilation
            data['parameters']['ceil_mode'] = node.ceil_mode
            data['parameters']['return_indices'] = node.return_indices
        elif isinstance(node, BatchNormNode):
            data['name'] = 'Batch Normalization'
            data['category'] = 'Normalization layers'
            data['parameters'] = dict()
            data['parameters']['num_features'] = node.num_features
            data['parameters']['weight'] = node.weight
            data['parameters']['bias'] = node.bias
            data['parameters']['running_mean'] = node.running_mean
            data['parameters']['running_var'] = node.running_var
            data['parameters']['eps'] = node.eps
            data['parameters']['momentum'] = node.momentum
            data['parameters']['affine'] = node.affine
            data['parameters']['track_running_stats'] = node.track_running_stats
        elif isinstance(node, LRNNode):
            data['name'] = 'LRN'
            data['category'] = 'Normalization layers'
            data['parameters'] = dict()
            data['parameters']['size'] = node.size
            data['parameters']['alpha'] = node.alpha
            data['parameters']['beta'] = node.beta
            data['parameters']['k'] = node.k
        elif isinstance(node, DropoutNode):
            data['name'] = 'Dropout'
            data['category'] = 'Dropout layers'
            data['parameters'] = dict()
            data['parameters']['p'] = node.p
        elif isinstance(node, UnsqueezeNode):
            data['name'] = 'Unsqueeze'
            data['category'] = 'Utility layers'
            data['parameters'] = dict()
            data['parameters']['axes'] = node.axes
        elif isinstance(node, FlattenNode):
            data['name'] = 'Flatten'
            data['category'] = 'Utility layers'
            data['parameters'] = dict()
            data['parameters']['axis'] = node.axis
        elif isinstance(node, ReshapeNode):
            data['name'] = 'Reshape'
            data['category'] = 'Utility layers'
            data['parameters'] = dict()
            data['parameters']['shape'] = node.shape
            data['parameters']['allow_zero'] = node.allow_zero

        if data['parameters']:
            for data_key, data_value in data['parameters'].items():
                if type(data_value) is not str:
                    data['parameters'][data_key] = str(data_value)

        return data, node.identifier
