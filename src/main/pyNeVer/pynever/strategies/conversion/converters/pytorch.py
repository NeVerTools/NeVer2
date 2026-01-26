import pynever.strategies.conversion.converters.pytorch_layers as pyt_l
from pynever.strategies.conversion.representation import ConversionStrategy, PyTorchNetwork
from pynever.strategies.conversion.converters.pytorch_tracer import PytL_Tracer
import torch
import torch.nn as nn
import operator
import pynever.networks as networks
import pynever.nodes as nodes

class PytorchAcyclicNetworkFactory(nn.Module) :

    def __init__(self, identifier: str, modules: dict, dependencies: dict, input_ids: list[str], output_id: str):
        super().__init__()
        self.identifier = identifier
        self.module_dict = nn.ModuleDict(modules)
        self.dependencies = dependencies
        self.input_ids = input_ids
        self.output_id = output_id

    def forward(self, x):
        outputs = {}
        for input_id in self.input_ids:
            outputs[input_id] = x

        #dependencies will always be sorted with a topological sort (lazy topological traversal)
        for input, input_dependecies in self.dependencies.items():
            if isinstance(input_dependecies, list) : #if the dependencies (parent) are a list, then it's an add or a concat
                param = [outputs[id] if id in outputs.keys() else x for id in input_dependecies]
                outputs[input] = self.module_dict[input](*param)
            else : #in that case, it's always nodes with only one dependency
                param = outputs[input_dependecies] if input_dependecies in outputs.keys() else x
                outputs[input] = self.module_dict[input](param)
        return outputs[self.output_id]

class PyTorchConverter(ConversionStrategy):
    """
    A class used to represent the conversion strategy for PyTorch models.

    Methods
    ----------
    from_neural_network(NeuralNetwork)
        Convert the neural network of interest to a PyTorchNetwork model.
    to_neural_network(PyTorchNetwork)
        Convert the PyTorchNetwork of interest to our internal representation of a Neural Network.

    """

    def __create_pytorch_module(self, current_node):
        """Create a PyTorch module from an internal node representation."""
        # Create a mapping of node types to their handler methods
        node_handlers = {
            nodes.ConcatNode: self.__create_concat_module,
            nodes.SumNode: self.__create_sum_module,
            nodes.ReLUNode: self.__create_relu_module,
            nodes.ELUNode: self.__create_elu_module,
            nodes.LeakyReLUNode: self.__create_leakyrelu_module,
            nodes.CELUNode: self.__create_celu_module,
            nodes.SigmoidNode: self.__create_sigmoid_module,
            nodes.TanhNode: self.__create_tanh_module,
            nodes.FullyConnectedNode: self.__create_linear_module,
            nodes.BatchNormNode: self.__create_batchnorm_module,
            nodes.ConvNode: self.__create_conv_module,
            nodes.AveragePoolNode: self.__create_averagepool_module,
            nodes.MaxPoolNode: self.__create_maxpool_module,
            nodes.SoftMaxNode: self.__create_softmax_module,
            nodes.UnsqueezeNode: self.__create_unsqueeze_module,
            nodes.ReshapeNode: self.__create_reshape_module,
            nodes.FlattenNode: self.__create_flatten_module,
            nodes.DropoutNode: self.__create_dropout_module,
            nodes.LRNNode: self.__create_lrn_module,
        }
        
        node_type = type(current_node)
        if node_type not in node_handlers:
            raise NotImplementedError(f"Node type {node_type} not implemented during PyTorch module creation")
        
        # Execute the handler for this node type
        module = node_handlers[node_type](current_node)
        return module

    # Handler methods for each node type
    @staticmethod
    def __create_concat_module(current_node):
        """Create ConcatModule."""
        axis = current_node.axis + 1 if current_node.axis >= 0 else current_node.axis
        module = pyt_l.ConcatModule(current_node.identifier, current_node.get_input_dim(), current_node.out_dim, axis)
        return module

    @staticmethod
    def __create_sum_module(current_node):
        """Create SumModule."""
        module = pyt_l.SumModule(current_node.identifier, current_node.get_input_dim(), current_node.out_dim)
        return module

    @staticmethod
    def __create_relu_module(current_node):
        """Create ReLU module."""
        module = pyt_l.ReLU(current_node.identifier, current_node.get_input_dim(), current_node.out_dim)
        return module


    @staticmethod
    def __create_elu_module(current_node):
        """Create ELU module."""
        module = pyt_l.ELU(current_node.identifier, current_node.get_input_dim(), current_node.out_dim, current_node.alpha)
        return module


    @staticmethod
    def __create_leakyrelu_module(current_node):
        """Create LeakyReLU module."""
        module = pyt_l.LeakyReLU(current_node.identifier, current_node.get_input_dim(), current_node.out_dim, current_node.negative_slope)
        return module


    @staticmethod
    def __create_celu_module(current_node):
        """Create CELU module."""
        module = pyt_l.CELU(current_node.identifier, current_node.get_input_dim(), current_node.out_dim, current_node.alpha)
        return module


    @staticmethod
    def __create_sigmoid_module(current_node):
        """Create Sigmoid module."""
        module = pyt_l.Sigmoid(current_node.identifier, current_node.get_input_dim(), current_node.out_dim)
        return module


    @staticmethod
    def __create_tanh_module(current_node):
        """Create Tanh module."""
        module = pyt_l.Tanh(current_node.identifier, current_node.get_input_dim(), current_node.out_dim)
        return module


    @staticmethod
    def __create_linear_module(current_node):
        """Create Linear (FullyConnected) module."""
        has_bias = current_node.bias is not None

        module = pyt_l.Linear(
            identifier=current_node.identifier,
            in_dim=current_node.get_input_dim(),
            out_dim=current_node.out_dim,
            in_features=current_node.in_features,
            out_features=current_node.out_features,
            bias=has_bias
        )
        
        module.weight.data = current_node.weight.clone()
        if has_bias:
            module.bias.data = current_node.bias.clone()
        
        return module


    @staticmethod
    def __create_batchnorm_module(current_node):
        """Create BatchNorm module (1d, 2d, or 3d based on input dimensions)."""
        input_dim_len = len(current_node.get_input_dim())
        
        if input_dim_len == 1 or input_dim_len == 2:
            module = pyt_l.BatchNorm1d(
                current_node.identifier,
                current_node.get_input_dim(),
                current_node.out_dim,
                num_features=current_node.num_features,
                eps=current_node.eps,
                momentum=current_node.momentum,
                affine=current_node.affine,
                track_running_stats=current_node.track_running_stats
            )
        elif input_dim_len == 3:
            module = pyt_l.BatchNorm2d(
                current_node.identifier,
                current_node.get_input_dim(),
                current_node.out_dim,
                num_features=current_node.num_features,
                eps=current_node.eps,
                momentum=current_node.momentum,
                affine=current_node.affine,
                track_running_stats=current_node.track_running_stats
            )
        elif input_dim_len == 4:
            module = pyt_l.BatchNorm3d(
                current_node.identifier,
                current_node.get_input_dim(),
                current_node.out_dim,
                num_features=current_node.num_features,
                eps=current_node.eps,
                momentum=current_node.momentum,
                affine=current_node.affine,
                track_running_stats=current_node.track_running_stats
            )
        else:
            raise Exception(
                "Pytorch does not support batchnorm layer for input with more than "
                "4 or less than 1 dimension excluding the batch dimension"
            )
        
        module.weight.data = current_node.weight.clone()
        module.bias.data = current_node.bias.clone()
        module.running_mean.data = current_node.running_mean.clone()
        module.running_var.data = current_node.running_var.clone()
        
        return module


    @staticmethod
    def __create_conv_module(current_node):
        """Create Conv module (1d, 2d, or 3d based on input dimensions)."""
        # Pytorch support only symmetric padding, therefore we assume that the padding given is symmetric
        padding = current_node.padding[:int(len(current_node.padding) / 2)]
        input_dim_len = len(current_node.get_input_dim())
        
        if input_dim_len == 2:
            module = pyt_l.Conv1d(
                current_node.identifier,
                current_node.get_input_dim(),
                current_node.out_dim,
                current_node.in_channels,
                current_node.out_channels,
                current_node.kernel_size,
                current_node.stride,
                padding,
                current_node.dilation,
                current_node.groups,
                current_node.has_bias
            )
        elif input_dim_len == 3:
            module = pyt_l.Conv2d(
                current_node.identifier,
                current_node.get_input_dim(),
                current_node.out_dim,
                current_node.in_channels,
                current_node.out_channels,
                current_node.kernel_size,
                current_node.stride,
                padding,
                current_node.dilation,
                current_node.groups,
                current_node.has_bias
            )
        elif input_dim_len == 4:
            module = pyt_l.Conv3d(
                current_node.identifier,
                current_node.get_input_dim(),
                current_node.out_dim,
                current_node.in_channels,
                current_node.out_channels,
                current_node.kernel_size,
                current_node.stride,
                padding,
                current_node.dilation,
                current_node.groups,
                current_node.has_bias
            )
        else:
            raise Exception(
                "Pytorch does not support Conv layer for input with more than "
                "4 or less than 2 dimension excluding the batch dimension"
            )
        
        module.weight.data = current_node.weight.clone()
        if current_node.has_bias:
            module.bias.data = current_node.bias.clone()
        
        return module


    @staticmethod
    def __create_averagepool_module(current_node):
        """Create AvgPool module (1d, 2d, or 3d based on input dimensions)."""
        # Pytorch support only symmetric padding, therefore we assume that the padding given is symmetric
        padding = current_node.padding[:int(len(current_node.padding) / 2)]
        input_dim_len = len(current_node.get_input_dim())
        
        if input_dim_len == 2:
            module = pyt_l.AvgPool1d(
                current_node.identifier,
                current_node.get_input_dim(),
                current_node.out_dim,
                current_node.kernel_size,
                current_node.stride,
                padding,
                current_node.ceil_mode,
                current_node.count_include_pad
            )
        elif input_dim_len == 3:
            module = pyt_l.AvgPool2d(
                current_node.identifier,
                current_node.get_input_dim(),
                current_node.out_dim,
                current_node.kernel_size,
                current_node.stride,
                padding,
                current_node.ceil_mode,
                current_node.count_include_pad
            )
        elif input_dim_len == 4:
            module = pyt_l.AvgPool3d(
                current_node.identifier,
                current_node.get_input_dim(),
                current_node.out_dim,
                current_node.kernel_size,
                current_node.stride,
                padding,
                current_node.ceil_mode,
                current_node.count_include_pad
            )
        else:
            raise Exception(
                "Pytorch does not support AvgPool layer for input with more than "
                "4 or less than 2 dimension excluding the batch dimension"
            )
        
        return module


    @staticmethod
    def __create_maxpool_module(current_node):
        """Create MaxPool module (1d, 2d, or 3d based on input dimensions)."""
        # Pytorch support only symmetric padding, therefore we assume that the padding given is symmetric
        padding = current_node.padding[:int(len(current_node.padding) / 2)]
        input_dim_len = len(current_node.get_input_dim())
        
        if input_dim_len == 2:
            module = pyt_l.MaxPool1d(
                current_node.identifier,
                current_node.get_input_dim(),
                current_node.out_dim,
                current_node.kernel_size,
                current_node.stride,
                padding,
                current_node.dilation,
                current_node.return_indices,
                current_node.ceil_mode
            )
        elif input_dim_len == 3:
            module = pyt_l.MaxPool2d(
                current_node.identifier,
                current_node.get_input_dim(),
                current_node.out_dim,
                current_node.kernel_size,
                current_node.stride,
                padding,
                current_node.dilation,
                current_node.return_indices,
                current_node.ceil_mode
            )
        elif input_dim_len == 4:
            module = pyt_l.MaxPool3d(
                current_node.identifier,
                current_node.get_input_dim(),
                current_node.out_dim,
                current_node.kernel_size,
                current_node.stride,
                padding,
                current_node.dilation,
                current_node.return_indices,
                current_node.ceil_mode
            )
        else:
            raise Exception(
                "Pytorch does not support MaxPool layer for input with more than "
                "4 or less than 2 dimension excluding the batch dimension"
            )
        
        return module


    @staticmethod
    def __create_softmax_module(current_node):
        """Create Softmax module."""
        # We need to scale the axis by one since our representation does not support the batch dimension
        module = pyt_l.Softmax(current_node.identifier, current_node.get_input_dim(), current_node.out_dim, current_node.axis + 1)
        return module


    @staticmethod
    def __create_unsqueeze_module(current_node):
        """Create Unsqueeze module."""
        # Our representation does not consider batch dimension, therefore we need to scale the axes values
        axes = tuple([e + 1 for e in current_node.axes])
        module = pyt_l.Unsqueeze(current_node.identifier, current_node.get_input_dim(), current_node.out_dim, axes)
        return module


    @staticmethod
    def __create_reshape_module(current_node):
        """Create Reshape module."""
        # Pytorch does not support the allow_zero attribute and the corresponding reshape with 0 dimensions
        if current_node.allow_zero:
            raise Exception("allow_zero not supported by pytorch")
        
        # Our representation does not consider batch dimension, therefore we need to add it to the shape
        shape = [1]
        for e in current_node.shape:
            shape.append(e)
        shape = tuple(shape)
        
        module = pyt_l.Reshape(current_node.identifier, current_node.get_input_dim(), current_node.out_dim, shape)
        return module


    @staticmethod
    def __create_flatten_module(current_node):
        """Create Flatten module."""
        # We need to scale the axis by one since our representation does not support the batch dimension
        module = pyt_l.Flatten(current_node.identifier, current_node.get_input_dim(), current_node.out_dim, current_node.axis + 1)
        return module


    @staticmethod
    def __create_dropout_module(current_node):
        """Create Dropout module."""
        module = pyt_l.Dropout(current_node.identifier, current_node.get_input_dim(), current_node.out_dim, current_node.p)
        return module
    
    @staticmethod
    def __create_lrn_module(current_node):
        """Create LocalResponseNormModule."""
        module = pyt_l.LocalResponseNorm(current_node.identifier, current_node.get_input_dim(), current_node.out_dim, current_node.size, current_node.alpha, current_node.beta, current_node.k)
        return module

    def from_neural_network(self, network: networks.NeuralNetwork) -> PyTorchNetwork:
        """
        Convert the neural network of interest to a PyTorch representation.

        Parameters
        ----------
        network : NeuralNetwork
            The neural network to convert.

        Returns
        ----------
        PyTorchNetwork
            The PyTorch representation resulting from the conversion of the original network.

        """
        pytorch_network = None
        alt_net = None
        if isinstance(network, networks.SequentialNetwork):
            pytorch_layers = []
            for layer in network.nodes.values():
                
                new_layer = self.__create_pytorch_module(layer)

                if new_layer is not None:
                    pytorch_layers.append(new_layer)

            pytorch_network = pyt_l.Sequential(network.identifier, network.get_input_id(), pytorch_layers)

            if pytorch_network is None:
                raise Exception("WARNING: network to convert is not valid, the alternative representation is None")

        elif isinstance(network, networks.AcyclicNetwork):
            child_depth = []
            current_depth = network.get_roots()
            can_treat_the_node = True
            visited = set()  # Using set because it don't take doublons, and is faster to verify the "in" condition
            modules = {}
            dependencies = {}
            
            while current_depth:
                for current_node in current_depth:
                    # Check if all parents have been visited
                    node_parent = network.get_parents(current_node)
                    for node in node_parent:
                        if node not in visited:  # If a parent has not been added, treat this node later
                            can_treat_the_node = False
                            if current_node not in child_depth:
                                child_depth.append(current_node)
                    
                    if current_node in visited:  # Avoid adding the same node twice
                        can_treat_the_node = False

                    # If all parents have been seen and the node has not been added: then treat this node
                    if can_treat_the_node:
                        # Add input_ids
                        current_inputs = network.get_input_ids_by_node(current_node)

                        # Add parents
                        current_inputs += [input.identifier for input in network.get_parents(current_node)]
                        
                        # Used only for single-input layers
                        current_input = str(current_inputs[0])

                        module = self.__create_pytorch_module(current_node)

                        if isinstance(current_node, nodes.ConcatNode) or isinstance(current_node, nodes.SumNode):
                            deps = current_inputs
                        else:
                            deps = current_input

                        if module is not None:
                            modules[current_node.identifier] = module
                            dependencies[current_node.identifier] = deps

                        # Add the node to the visited set, and add its children to the queue
                        visited.add(current_node)
                        for child in network.get_children(current_node):
                            if child not in child_depth:
                                child_depth.append(child)

                    else:  # We skipped this node, now we reset the can_treat_the_node condition
                        can_treat_the_node = True
                
                current_depth = child_depth
                child_depth = []

            pytorch_network = PytorchAcyclicNetworkFactory(
                network.identifier, 
                modules, 
                dependencies, 
                network.input_ids[list(network.input_ids.keys())[0]], 
                list(dependencies.keys())[-1]
            )

        # ask for network saving preference
        while True:
            print('Do you want to save your PyTorch model as a traced model? (y/n):')
            trace = input().strip().lower()
            if trace in ("y", "n"):
                break
            print("Invalid choice, please enter 'y' or 'n'.")

        if trace == "y": 
            tracer = PytL_Tracer()
            graph = tracer.trace(pytorch_network)
            pytorch_network = torch.fx.GraphModule(pytorch_network, graph)

        alt_net = PyTorchNetwork(network.identifier, pytorch_network)

        return alt_net
         
    def __get_module_from_node(self, node):
        """Helper method to get the actual module instance from a call_module node."""
        # The node.target is the module path (e.g., 'layer1.conv')
        module_path = node.target.split('.')
        module = self.pytorch_network if hasattr(self, 'pytorch_network') else node.graph.owning_module
        
        for attr in module_path:
            module = getattr(module, attr)
        
        return module
    
    @staticmethod
    def __process_skip_node(node, in_dim):
        """ This node is not relevant for verification and should not appear at all in benchmarks """
        return None

    @staticmethod
    def __process_relu(node, in_dim, module):
        """Process ReLU node."""
        return nodes.ReLUNode(node.name, in_dim)

    @staticmethod
    def __process_elu(node, in_dim, module):
        """Process ELU node."""
        return nodes.ELUNode(node.name, in_dim, module.alpha)

    @staticmethod
    def __process_leaky_relu(node, in_dim, module):
        """Process LeakyReLU node."""
        return nodes.LeakyReLUNode(node.name, in_dim, module.negative_slope)

    @staticmethod
    def __process_celu(node, in_dim, module):
        """Process CELU node."""
        return nodes.CELUNode(node.name, in_dim, module.alpha)

    @staticmethod
    def __process_sigmoid(node, in_dim, module):
        """Process Sigmoid node."""
        return nodes.SigmoidNode(node.name, in_dim)

    @staticmethod
    def __process_tanh(node, in_dim, module):
        """Process Tanh node."""
        return nodes.TanhNode(node.name, in_dim)

    @staticmethod
    def __process_gemm(node, in_dim, module):
        """Process Linear node."""
        out_features = module.out_features
        weight = module.weight
        bias = None
        has_bias = False
        if module.bias is not None:
            bias = module.bias
            has_bias = True
        return nodes.FullyConnectedNode(node.name, in_dim, out_features, weight, bias, has_bias)

    @staticmethod
    def __process_batch_norm(node, in_dim, module):
        """Process BatchNormalization node."""
        eps = module.eps
        momentum = module.momentum
        track_running_stats = module.track_running_stats
        affine = module.affine

        weight = module.weight
        bias = module.bias
        running_mean = module.running_mean
        running_var = module.running_var

        return nodes.BatchNormNode(node.name, in_dim, weight,
                                        bias, running_mean, running_var, eps, momentum, affine,
                                        track_running_stats)

    @staticmethod
    def __process_conv(node, in_dim, module):
        """Process Conv node."""
        # Get expected spatial dimensions (Conv1d=1, Conv2d=2, Conv3d=3)
        expected_spatial_dims = len(in_dim) - 1  # Exclude channel dimension
        
        # Helper to normalize int to tuple of correct length
        def normalize_param(value, expected_len):
            if isinstance(value, int):
                return (value,) * expected_len
            else:
                return tuple(value)
        
        out_channels = module.out_channels
        kernel_size = normalize_param(module.kernel_size, expected_spatial_dims)
        stride = normalize_param(module.stride, expected_spatial_dims)
        dilation = normalize_param(module.dilation, expected_spatial_dims)
        
        # For padding, duplicate each element (left, right, top, bottom, etc.)
        padding_normalized = normalize_param(module.padding, expected_spatial_dims)
        padding = tuple(list(padding_normalized) + list(padding_normalized))
        
        groups = module.groups
        weight = module.weight
        
        if module.bias is None:
            has_bias = False
            bias = None
        else:
            has_bias = True
            bias = module.bias

        return nodes.ConvNode(node.name, in_dim, out_channels, kernel_size,
                            stride, padding, dilation, groups, has_bias, bias, weight)

    @staticmethod
    def __process_average_pool(node, in_dim, module):
        """Process AveragePool node."""
        # Get expected spatial dimensions
        expected_spatial_dims = len(in_dim) - 1  # Exclude channel dimension
        
        # Helper to normalize int to tuple of correct length
        def normalize_param(value, expected_len):
            if isinstance(value, int):
                return (value,) * expected_len  # Repeat int for each spatial dim
            else:
                return tuple(value)
        
        kernel_size = normalize_param(module.kernel_size, expected_spatial_dims)
        stride = normalize_param(module.stride, expected_spatial_dims)
        
        # For padding, duplicate each element
        padding_normalized = normalize_param(module.padding, expected_spatial_dims)
        padding = tuple(list(padding_normalized) + list(padding_normalized))
        
        ceil_mode = module.ceil_mode
        count_include_pad = module.count_include_pad

        return nodes.AveragePoolNode(node.name, in_dim, kernel_size, stride, padding,
                                            ceil_mode, count_include_pad)

    @staticmethod
    def __process_max_pool(node, in_dim, module):
        """Process MaxPool node."""
        
        # Get expected spatial dimensions
        expected_spatial_dims = len(in_dim) - 1  # Exclude channel dimension
        
        # Helper to normalize int to tuple of correct length
        def normalize_param(value, expected_len):
            if isinstance(value, int):
                return (value,) * expected_len  # Repeat int for each spatial dim
            else:
                return tuple(value)
        
        kernel_size = normalize_param(module.kernel_size, expected_spatial_dims)
        stride = normalize_param(module.stride, expected_spatial_dims)
        dilation = normalize_param(module.dilation, expected_spatial_dims)
        
        # For padding, duplicate each element
        padding_normalized = normalize_param(module.padding, expected_spatial_dims)
        padding = tuple(list(padding_normalized) + list(padding_normalized))

        ceil_mode = module.ceil_mode
        return_indices = module.return_indices

        return nodes.MaxPoolNode(node.name, in_dim, kernel_size, stride, padding, dilation,
                                        ceil_mode, return_indices)

    @staticmethod
    def __process_lrn(node, in_dim, module):
        """Process LRN node."""
        return nodes.LRNNode(node.name, in_dim, module.size, module.alpha, module.beta, module.k)

    @staticmethod
    def __process_softmax(node, in_dim, module):
        """Process Softmax node."""
        # Since the ONNX representation consider the batch dimension we need to scale the axis by 1
        # when we pass to our representation.

        return nodes.SoftMaxNode(node.name, in_dim, module.dim-1)

    @staticmethod
    def __process_unsqueeze(node, in_dim):
        """Process Unsqueeze node."""
        if len(node.args) > 1 and node.args[1] is not None:
            dim = node.args[1]
        elif 'dim' in node.kwargs:
            dim = node.kwargs['dim']
        else:
            dim = 0
        
        dim = [dim] if isinstance(dim, int) else dim

        axes = tuple([e - 1 for e in dim])        

        return nodes.UnsqueezeNode(node.name, in_dim, axes)

    @staticmethod
    def __process_flatten(node, in_dim, module):
        """Process Flatten node."""
        # Adjust dims: PyTorch includes batch (dim 0), but in_dim doesn't
        # So we need to shift all dimension indices down by 1
        start_dim = module.start_dim
        end_dim = module.end_dim
        
        # Adjust for missing batch dimension
        if start_dim > 0:
            start_dim -= 1
        # If start_dim was 0 (batch dim in PyTorch), treat it as 0 in our representation
        # which means we're flattening from the first actual dimension
        if start_dim < 0:
            start_dim = 0
        
        if end_dim >= 0:
            end_dim -= 1
        # end_dim = -1 in PyTorch means "last dim", same in our representation
        
        input_shape = in_dim
        rank = len(input_shape)
        
        # Handle negative indices
        if start_dim < 0:
            start_dim = rank + start_dim
        if end_dim < 0:
            end_dim = rank + end_dim
        
        # Build new shape
        new_shape = []
        
        # Keep dimensions before start_dim
        new_shape.extend(input_shape[:start_dim])
        
        # Flatten dimensions [start_dim, end_dim]
        flattened_size = 1
        for i in range(start_dim, min(end_dim + 1, rank)):
            flattened_size *= input_shape[i]
        new_shape.append(flattened_size)
        
        # Keep dimensions after end_dim
        if end_dim + 1 < rank:
            new_shape.extend(input_shape[end_dim + 1:])
        
        if len(new_shape) == 1:
            shape = (new_shape[0],)
        else:
            shape = tuple(new_shape)
        
        return nodes.ReshapeNode(node.name, in_dim, shape)
    
    @staticmethod
    def __process_reshape(node, in_dim, module):
        """Process Add node."""
        return nodes.ReshapeNode(node.name, in_dim, module.shape, allow_zero=True) # in pytorch the zero value is always honored

    @staticmethod
    def __process_dropout(node, in_dim, module):
        """Process Dropout node."""
        return nodes.DropoutNode(node.name, in_dim, module.p)
    
    @staticmethod
    def __process_add(node, in_dim):
        """Process Add node."""
        return nodes.SumNode(node.name, in_dim)

    @staticmethod
    def __process_concat(node, in_dim):
        """Process Concat node."""
        dim = node.kwargs.get('dim', None) # in pytorch axis is called dim
    
        # If not in kwargs, check args
        if dim is None and len(node.args) > 1:
            dim = node.args[1]
        
        # Default to 0 if not specified (torch.cat default)
        if dim is None:
            dim = 0

        if dim > 0: # assumption: concatenation is not performed on the batch (axis 0)
            dim = dim - 1
        return nodes.ConcatNode(node.name, in_dim, axis=dim)
    
    def __process_node(self, node, in_dim):
        """Process a single PyTorch FX node and return the corresponding internal node."""
        
        # Create a mapping of node operations/targets to their handler methods
        new_node = None

        # Handle different node operation types
        if node.op == 'call_function':
            # Node calls a function directly (e.g., torch.relu, torch.add)
            function_handlers = {
                torch.cat: self.__process_concat,
                operator.add: self.__process_add,
                torch.sum: self.__process_add,
                torch.stack: self.__process_skip_node,
                torch.unsqueeze: self.__process_unsqueeze,
            }
            
            if node.target in function_handlers:
                new_node = function_handlers[node.target](node, in_dim)
            else:
                raise NotImplementedError(f"Function {node.target} not implemented during the import of pytorch networks")

        elif node.op == 'call_module':
            # Node calls a module (e.g., nn.Linear, nn.Conv2d)
            # We need to get the actual module from the traced graph
            module = self.__get_module_from_node(node)
            
            module_handlers = {
                # Linear / GEMM
                pyt_l.Linear: self.__process_gemm,
                torch.nn.Linear: self.__process_gemm,

                # Convolution
                torch.nn.Conv3d: self.__process_conv,
                torch.nn.Conv2d: self.__process_conv,
                torch.nn.Conv1d: self.__process_conv,
                pyt_l.Conv1d: self.__process_conv,
                pyt_l.Conv2d: self.__process_conv,
                pyt_l.Conv3d: self.__process_conv,

                # BatchNorm
                torch.nn.BatchNorm3d: self.__process_batch_norm,
                torch.nn.BatchNorm2d: self.__process_batch_norm,
                torch.nn.BatchNorm1d: self.__process_batch_norm,
                pyt_l.BatchNorm3d: self.__process_batch_norm,
                pyt_l.BatchNorm2d: self.__process_batch_norm,
                pyt_l.BatchNorm1d: self.__process_batch_norm,

                # Activations
                torch.nn.ReLU: self.__process_relu,
                pyt_l.ReLU: self.__process_relu,
                torch.nn.ELU: self.__process_elu,
                pyt_l.ELU: self.__process_elu,
                torch.nn.LeakyReLU: self.__process_leaky_relu,
                pyt_l.LeakyReLU: self.__process_leaky_relu,
                torch.nn.CELU: self.__process_celu,
                pyt_l.CELU: self.__process_celu,
                torch.nn.Sigmoid: self.__process_sigmoid,
                pyt_l.Sigmoid: self.__process_sigmoid,
                torch.nn.Tanh: self.__process_tanh,
                pyt_l.Tanh: self.__process_tanh,

                # Average Pooling
                torch.nn.AvgPool3d: self.__process_average_pool,
                torch.nn.AvgPool2d: self.__process_average_pool,
                torch.nn.AvgPool1d: self.__process_average_pool,
                pyt_l.AvgPool3d: self.__process_average_pool,
                pyt_l.AvgPool2d: self.__process_average_pool,
                pyt_l.AvgPool1d: self.__process_average_pool,

                # Max Pooling
                torch.nn.MaxPool3d: self.__process_max_pool,
                torch.nn.MaxPool2d: self.__process_max_pool,
                torch.nn.MaxPool1d: self.__process_max_pool,
                pyt_l.MaxPool3d: self.__process_max_pool,
                pyt_l.MaxPool2d: self.__process_max_pool,
                pyt_l.MaxPool1d: self.__process_max_pool,

                # Softmax
                torch.nn.Softmax: self.__process_softmax,
                pyt_l.Softmax: self.__process_softmax,

                # Flatten
                torch.nn.Flatten: self.__process_flatten,
                pyt_l.Flatten: self.__process_flatten,

                # Reshape
                pyt_l.Reshape: self.__process_reshape,

                # Dropout
                torch.nn.Dropout: self.__process_dropout,
                pyt_l.Dropout: self.__process_dropout,

                # Local Response Norm
                torch.nn.LocalResponseNorm: self.__process_lrn,
                pyt_l.LocalResponseNorm: self.__process_lrn,
            }
            
            module_type = type(module)
            if module_type in module_handlers:
                new_node = module_handlers[module_type](node, in_dim, module)
            else:
                raise NotImplementedError(f"Module type {module_type} not implemented during the import of pytorch networks")
        
        elif node.op == 'call_method':
            
            # Node calls a method on a tensor (e.g., tensor.reshape, tensor.view)
            method_handlers = {
                'unsqueeze': self.__process_unsqueeze,
            }
            
            if node.target in method_handlers:
                new_node = method_handlers[node.target](node, in_dim)
            else:
                raise NotImplementedError(f"Method {node.target} not implemented during the import of pytorch networks")

        else:
            raise NotImplementedError(f"Node operation type {node.op} not implemented during the import of pytorch networks")
        
        return new_node
    
    @staticmethod
    def __is_sequential_pytorch(alt_rep: PyTorchNetwork) -> bool:
        """
        Determine whether the given PyTorch network is sequential.

        Parameters
        ----------
        alt_rep : PyTorchNetwork
            The PyTorch network representation to analyze. Its `pytorch_network`
            attribute is expected to be a `torch.fx.GraphModule`.

        Returns
        -------
        bool
            True if the network's FX graph is sequential (i.e., strictly feed-forward
            with a single execution path), False otherwise.
        """

        # if the network is not traced, trace it
        if not isinstance(alt_rep.pytorch_network, torch.fx.GraphModule):
            torch_graph = torch.fx.symbolic_trace(alt_rep.pytorch_network).graph
        else: 
            torch_graph = alt_rep.pytorch_network.graph

        # Get input nodes
        input_nodes = [node for node in torch_graph.nodes if node.op == 'placeholder']
        if len(input_nodes) > 1:
            return False
        
        # Get output nodes
        output_nodes = [node for node in torch_graph.nodes if node.op == 'output']
        if len(output_nodes) > 1:
            return False

        # Track the number of parents
        usage_counter = {}
        
        for node in torch_graph.nodes:
            # Initialize counter for this node
            if node.name not in usage_counter:
                usage_counter[node.name] = 0
            
            # Count how many parents the node has
            for arg in node.args:
                if isinstance(arg, torch.fx.Node):
                    arg_name = arg.name
                    if arg_name not in usage_counter:
                        usage_counter[arg_name] = 0
                    usage_counter[arg_name] += 1
                    
                    # If any node is used more than once, it's not sequential
                    if usage_counter[arg_name] > 1:
                        return False
            
            # Also check kwargs for parent counting
            for arg in node.kwargs.values():
                if isinstance(arg, torch.fx.Node):
                    arg_name = arg.name
                    if arg_name not in usage_counter:
                        usage_counter[arg_name] = 0
                    usage_counter[arg_name] += 1
                    
                    if usage_counter[arg_name] > 1:
                        return False
        
        return True
    
    @staticmethod
    def __pytorch_extract_input_shapes(alt_rep: PyTorchNetwork, include_parameters=False):
        """
        Build a dict mapping each external input (and optionally parameter) 
        name to its shape as a tuple.

        Parameters
        ----------
        alt_rep : PytorchNetwork
            The PyTorch model with traced graph.
        include_parameters : bool
            If True, also include model parameters and buffers.

        Returns
        -------
        dict[str, tuple[int|str|None]]
            Mapping input/parameter names -> shape tuple.
            Dimensions may be int, str (symbolic), or None (unknown).
        """
        traced_graph = alt_rep.pytorch_network.graph
        model = alt_rep.pytorch_network
        
        shape_dict = {}
        
        # Get all placeholder nodes (these are the actual inputs)
        placeholder_nodes = [node for node in traced_graph.nodes if node.op == 'placeholder']
        
        # Get parameter names from get_attr nodes
        parameter_names = {node.target for node in traced_graph.nodes if node.op == 'get_attr'}
        
        # Extract shapes from placeholder nodes
        for node in placeholder_nodes:
            # Try to get shape from metadata
            if hasattr(node, 'meta') and 'tensor_meta' in node.meta:
                tensor_meta = node.meta['tensor_meta']
                if hasattr(tensor_meta, 'shape'):
                    shape_dict[node.name] = tuple(tensor_meta.shape)
            elif hasattr(node, 'meta') and 'val' in node.meta:
                val = node.meta['val']
                if hasattr(val, 'shape'):
                    shape_dict[node.name] = tuple(val.shape)
            else:
                # If no metadata, set to None (unknown shape)
                shape_dict[node.name] = None
        
        # Optionally add parameters and buffers
        if include_parameters:
            # Add parameter shapes
            if hasattr(model, 'named_parameters'):
                for name, param in model.named_parameters():
                    shape_dict[name] = tuple(param.shape)
            
            # Add buffer shapes
            if hasattr(model, 'named_buffers'):
                for name, buffer in model.named_buffers():
                    shape_dict[name] = tuple(buffer.shape)
        else:
            # Exclude any placeholder nodes that are actually parameters
            # (though this should not happen in a properly traced graph)
            for name in list(shape_dict.keys()):
                if name in parameter_names:
                    del shape_dict[name]
        
        return shape_dict

    def __to_neural_network_sequential(self, alt_rep: PyTorchNetwork) -> networks.NeuralNetwork:
        """
        Convert the PyTorch representation of interest to the internal one.

        Parameters
        ----------
        alt_rep : PyTorchNetwork
            The PyTorch Representation to convert as '.

        Returns
        ----------
        NeuralNetwork
            The Neural Network resulting from the conversion of PyTorch Representation.
        """
        identifier = alt_rep.identifier
        if hasattr(alt_rep.pytorch_network, 'input_id'):
            input_id = alt_rep.pytorch_network.input_id
        else:
            input_id = 'X'

        network = networks.SequentialNetwork(identifier, input_id)

        node_index = 0
        alt_rep.pytorch_network.cpu()

        # if the network is not traced, trace it
        if not isinstance(alt_rep.pytorch_network, torch.fx.GraphModule):
            torch_graph = torch.fx.symbolic_trace(alt_rep.pytorch_network).graph
        else: 
            torch_graph = alt_rep.pytorch_network.graph

        # WARNING: we asume the user does NOT specify the batch size
        print('Please provide input dimension for the network:')
        layer_in_dim = input()
        layer_in_dim = tuple(int(x.strip()) for x in layer_in_dim.split(','))

        for node in torch_graph.nodes:
            # Skip placeholder (input) and output nodes for now
            if node.op in ['placeholder', 'get_attr', 'output']:
                continue

            new_node = self.__process_node(node, layer_in_dim)               
            
            if new_node is not None:
                node_index += 1
                network.append_node(new_node)
                layer_in_dim = network.get_last_node().out_dim

        return network
    
    def __to_neural_network_acyclic(self, alt_rep: PyTorchNetwork) -> networks.AcyclicNetwork: 
        """
        Convert the Pytorch representation of interest to the internal one.
        It assumes the network to have an acyclic architectures (ResNet).

        Parameters
        ----------
        alt_rep : PytorchNetwork
            The PyTorch Representation to convert.
        input_shape : tuple
            The input shape of the network (excluding batch dimension).

        Returns
        ----------
        AcyclicNetwork
            The Acyclic Neural Network resulting from the conversion of PyTorch Representation.
        """

        # WARNING: we assume that the batch size is not specified
        print('Please provide input dimension for the network:')
        input_shape = input()
        input_shape = tuple(int(x.strip()) for x in input_shape.split(','))

        # Tracking dictionaries for acyclic network structure
        pytorch_to_internal = {}

        identifier = alt_rep.identifier

        # First phase: get the network structure and create the singular nodes - internal representation
        traced_graph = alt_rep.pytorch_network.graph

        pytorch_nodes = {}

        # Build the dictionary
        for node in traced_graph.nodes:
            # Skip placeholder (input) and output nodes for now
            if node.op in ['placeholder', 'output']:
                continue
            
            # Filter inputs: only keep actual tensor-producing nodes, exclude parameters
            filtered_inputs = set()
            for arg in node.args:
                if isinstance(arg, torch.fx.Node):
                    if arg.op != 'get_attr':  # Exclude parameter nodes
                        filtered_inputs.add(arg.name)

                #Handle lists/tuples of nodes (for cat, stack, etc.)
                elif isinstance(arg, (list, tuple)):
                    for item in arg:
                        if isinstance(item, torch.fx.Node):
                            if item.op != 'get_attr':
                                filtered_inputs.add(item.name)

            for arg in node.kwargs.values():
                if isinstance(arg, torch.fx.Node):
                    if arg.op != 'get_attr':
                        filtered_inputs.add(arg.name)

                #Handle lists/tuples in kwargs too
                elif isinstance(arg, (list, tuple)):
                    for item in arg:
                        if isinstance(item, torch.fx.Node):
                            if item.op != 'get_attr':
                                filtered_inputs.add(item.name)
            
            pytorch_nodes[node.name] = {
                "inputs": filtered_inputs,         
                "outputs": {node.name},            
                "children": set(),                 
                "parents": set(),                  
                "node": node                       
            }

        # Fill children and parents
        node_names = list(pytorch_nodes.keys())
        for n1 in node_names:
            for n1_out in pytorch_nodes[n1]["outputs"]:
                for n2 in node_names:
                    if n1_out in pytorch_nodes[n2]["inputs"]:
                        pytorch_nodes[n2]["parents"].add(n1)
                        pytorch_nodes[n1]["children"].add(n2)
        
        # DEBUG
        # print("\n=== GRAPH STRUCTURE ===")
        # for name, info in pytorch_nodes.items():
        #    print(f"{name}:")
        #    print(f"  parents: {info['parents']}")
        #    print(f"  children: {info['children']}")
        #    print(f"  inputs: {info['inputs']}")
        #print("======================\n")

        node_order = []

        # Create the internal representations
        for node in traced_graph.nodes:
            # Skip placeholder and output nodes
            if node.op in ['placeholder', 'output', 'get_attr']:
                continue

            identifier_of_node = node.name

            if identifier_of_node not in pytorch_nodes:
                continue

            if identifier_of_node in list(pytorch_to_internal.keys()):
                continue

            if all(parent in pytorch_to_internal for parent in pytorch_nodes[identifier_of_node]['parents']):
                in_dims = []

                # If the node has no parents it's an input node
                if len(pytorch_nodes[identifier_of_node]['parents']) == 0:
                    # Use the provided input shape
                    in_dims = [input_shape]
                else:
                    # Take the input dimensions from the parents
                    in_dims = [pytorch_to_internal[p].out_dim for p in pytorch_nodes[identifier_of_node]['parents']]

                if len(in_dims) == 1:
                    in_dims = in_dims[0]  # for compatibility reasons with sequential networks

                internal_representation_node = self.__process_node(node, in_dims)

                # If the layer has been skipped, rewire graph
                if not internal_representation_node:
                    # Rewire children
                    for child in list(pytorch_nodes[identifier_of_node]['children']):
                        pytorch_nodes[child]['parents'].discard(identifier_of_node)
                        pytorch_nodes[child]['parents'].update(pytorch_nodes[identifier_of_node]['parents'])

                        # Replace child's inputs: drop this node's outputs, add this node's inputs
                        pytorch_nodes[child]['inputs'].difference_update(pytorch_nodes[identifier_of_node]['outputs'])
                        pytorch_nodes[child]['inputs'].update(pytorch_nodes[identifier_of_node]['inputs'])

                    # Rewire parents
                    for parent in list(pytorch_nodes[identifier_of_node]['parents']):
                        pytorch_nodes[parent]['children'].discard(identifier_of_node)
                        pytorch_nodes[parent]['children'].update(pytorch_nodes[identifier_of_node]['children'])

                        # Replace parent's outputs: drop this node's outputs, add child's outputs
                        pytorch_nodes[parent]['outputs'].difference_update(pytorch_nodes[identifier_of_node]['outputs'])
                        for child in pytorch_nodes[identifier_of_node]['children']:
                            pytorch_nodes[parent]['outputs'].update(pytorch_nodes[child]['outputs'])
                    
                    # IMPORTANT: Mark this node as processed by adding a sentinel value
                    # This allows children to be processed even though we're not creating an internal node
                    pytorch_to_internal[identifier_of_node] = None
                else:
                    # Only add to pytorch_to_internal and node_order if node was actually created
                    pytorch_to_internal[identifier_of_node] = internal_representation_node
                    node_order.append(identifier_of_node)
            else:
                print(f'Warning: I cannot compute {identifier_of_node} following the pytorch DAG')

        # Second phase: link the nodes and build the actual network      
        network_input_shapes = self.__pytorch_extract_input_shapes(alt_rep, include_parameters=False)
        network_input_ids = list(network_input_shapes.keys())
        network = networks.AcyclicNetwork(identifier, input_ids=network_input_ids)

        for name in node_order:
            internal_representation = pytorch_to_internal[name]
            # Filter parents to only include those that exist in pytorch_to_internal and are not None
            parents = [pytorch_to_internal[p] for p in pytorch_nodes[name]['parents'] if p in pytorch_to_internal.keys() and pytorch_to_internal[p] is not None]
            # Check if inputs are in the network input IDs
            input_ids = [x for x in pytorch_nodes[name]['inputs'] if x in network_input_ids]
            children = None  # Not using right now

            network.add_node(internal_representation, parents, children, input_ids)

        return network

    def to_neural_network(self, alt_rep:PyTorchNetwork) -> networks.NeuralNetwork:
                
        internal_representation = None

        if self.__is_sequential_pytorch(alt_rep):
            internal_representation = self.__to_neural_network_sequential(alt_rep)
        else:
            internal_representation = self.__to_neural_network_acyclic(alt_rep)

        if not internal_representation:
            raise RuntimeError('Pytorch to internal representation parsing have failed')
        
        return internal_representation