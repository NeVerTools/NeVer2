import numpy as np
import onnx
import torch
from torch import Tensor

import pynever.networks as networks
import pynever.nodes as nodes
from pynever.strategies.conversion.representation import ConversionStrategy, ONNXNetwork

TORCH_TO_ONNX_DTYPE = {
    torch.float32: onnx.TensorProto.FLOAT,
    torch.float:   onnx.TensorProto.FLOAT,   # alias
    torch.float64: onnx.TensorProto.DOUBLE,
    torch.double:  onnx.TensorProto.DOUBLE,  # alias
    torch.float16: onnx.TensorProto.FLOAT16,

    torch.int64:   onnx.TensorProto.INT64,
    torch.long:    onnx.TensorProto.INT64,   # alias
    torch.int32:   onnx.TensorProto.INT32,
    torch.int16:   onnx.TensorProto.INT16,
    torch.int8:    onnx.TensorProto.INT8,

    torch.uint8:   onnx.TensorProto.UINT8,
    torch.bool:    onnx.TensorProto.BOOL,
}

class ONNXConverter(ConversionStrategy):
    """
    A class used to represent the conversion strategy for ONNX models.
    """

    @staticmethod
    def __add_onnx_averagepool(current_node: nodes.AveragePoolNode, current_input: str, current_output: str,
                               onnx_nodes: list):

        onnx_node = onnx.helper.make_node(
            'AveragePool',
            inputs=[current_input],
            outputs=[current_output],
            ceil_mode=int(current_node.ceil_mode),
            count_include_pad=int(current_node.count_include_pad),
            kernel_shape=list(current_node.kernel_size),
            strides=list(current_node.stride),
            pads=list(current_node.padding)
        )

        onnx_nodes.append(onnx_node)

    @staticmethod
    def __add_onnx_batchnorm(current_node: nodes.BatchNormNode, current_input: str, current_output: str,
                             onnx_nodes: list, input_info: list, initializers: list):

        input_scale = current_node.identifier + "_scale"
        input_bias = current_node.identifier + "_bias"
        input_mean = current_node.identifier + "_mean"
        input_var = current_node.identifier + "_var"

        scale_value_info = onnx.helper.make_tensor_value_info(input_scale, TORCH_TO_ONNX_DTYPE[current_node.weight.dtype],
                                                              [current_node.num_features])
        bias_value_info = onnx.helper.make_tensor_value_info(input_bias, TORCH_TO_ONNX_DTYPE[current_node.bias.dtype],
                                                             [current_node.num_features])
        mean_value_info = onnx.helper.make_tensor_value_info(input_mean, TORCH_TO_ONNX_DTYPE[current_node.running_mean.dtype],
                                                             [current_node.num_features])
        var_value_info = onnx.helper.make_tensor_value_info(input_var, TORCH_TO_ONNX_DTYPE[current_node.running_var.dtype],
                                                            [current_node.num_features])

        scale_tensor = onnx.numpy_helper.from_array(current_node.weight.detach().numpy(), input_scale)
        bias_tensor = onnx.numpy_helper.from_array(current_node.bias.detach().numpy(), input_bias)
        mean_tensor = onnx.numpy_helper.from_array(current_node.running_mean.detach().numpy(), input_mean)
        var_tensor = onnx.numpy_helper.from_array(current_node.running_var.detach().numpy(), input_var)

        onnx_node = onnx.helper.make_node(
            'BatchNormalization',
            inputs=[current_input, input_scale, input_bias, input_mean, input_var],
            outputs=[current_output],
            epsilon=current_node.eps,
            momentum=current_node.momentum,
            training_mode=int(current_node.track_running_stats)
        )

        input_info.append(scale_value_info)
        input_info.append(bias_value_info)
        input_info.append(mean_value_info)
        input_info.append(var_value_info)

        initializers.append(scale_tensor)
        initializers.append(bias_tensor)
        initializers.append(mean_tensor)
        initializers.append(var_tensor)

        onnx_nodes.append(onnx_node)

    @staticmethod
    def __add_onnx_celu(current_node: nodes.CELUNode, current_input: str, current_output: str,
                        onnx_nodes: list):

        onnx_node = onnx.helper.make_node(
            'Celu',
            inputs=[current_input],
            outputs=[current_output],
            alpha=current_node.alpha
        )

        onnx_nodes.append(onnx_node)

    @staticmethod
    def __add_onnx_concat(current_node: nodes.ConcatNode, current_inputs: list[str], current_output: str,
                          onnx_nodes: list):
        """
        Add a Concat node to the ONNX graph.
        All input tensors must have the same shape, except for the concatenation axis.

        Parameters
        ----------
        current_node : nodes.ConcatNode
            The concat node to convert.
        current_inputs : list[str]
            List of input identifiers to be concatenated.
        current_output : str
            The output identifier.
        onnx_nodes : list
            The list to append the ONNX node to.
        """
        axis = current_node.axis + 1 if current_node.axis >= 0 else current_node.axis
        onnx_node = onnx.helper.make_node(
            'Concat',
            inputs=current_inputs,
            outputs=[current_output],
            axis=axis,
            name=current_node.identifier
        )
        onnx_nodes.append(onnx_node)

    @staticmethod
    def __add_onnx_conv(current_node: nodes.ConvNode, current_input: str, current_output: str,
                        onnx_nodes: list, input_info: list, initializers: list):

        input_weight = current_node.identifier + "_weight"
        inputs = [current_input, input_weight]
        
        # Add weight
        input_info.append(onnx.helper.make_tensor_value_info(
            input_weight, TORCH_TO_ONNX_DTYPE[current_node.weight.dtype], list(current_node.weight.shape)))
        initializers.append(onnx.numpy_helper.from_array(current_node.weight.detach().numpy(), input_weight))
        
        # Add bias if present
        if current_node.has_bias:
            input_bias = current_node.identifier + "_bias"
            inputs.append(input_bias)
            input_info.append(onnx.helper.make_tensor_value_info(
                input_bias, TORCH_TO_ONNX_DTYPE[current_node.bias.dtype], list(current_node.bias.shape)))
            initializers.append(onnx.numpy_helper.from_array(current_node.bias.detach().numpy(), input_bias))

        onnx_nodes.append(onnx.helper.make_node(
            'Conv',
            inputs=inputs,
            outputs=[current_output],
            kernel_shape=list(current_node.kernel_size),
            strides=list(current_node.stride),
            dilations=list(current_node.dilation),
            group=current_node.groups,
            pads=list(current_node.padding)
        ))

    @staticmethod
    def __add_onnx_dropout(current_node: nodes.DropoutNode, current_input: str, current_output: str,
                           onnx_nodes: list, input_info: list, initializers: list):

        ratio_size = [1]
        input_ratio = current_node.identifier + "_ratio"

        ratio_value_info = onnx.helper.make_tensor_value_info(input_ratio, onnx.TensorProto.FLOAT,
                                                              ratio_size)

        ratio_tensor = onnx.numpy_helper.from_array(np.array([current_node.p]), input_ratio)

        onnx_node = onnx.helper.make_node(
            'Dropout',
            inputs=[current_input, input_ratio],
            outputs=[current_output]
        )

        input_info.append(ratio_value_info)
        initializers.append(ratio_tensor)

        onnx_nodes.append(onnx_node)

    @staticmethod
    def __add_onnx_elu(current_node: nodes.ELUNode, current_input: str, current_output: str,
                       onnx_nodes: list):

        onnx_node = onnx.helper.make_node(
            'Elu',
            inputs=[current_input],
            outputs=[current_output],
            alpha=current_node.alpha
        )

        onnx_nodes.append(onnx_node)

    @staticmethod
    def __add_onnx_flatten(current_node: nodes.FlattenNode, current_input: str, current_output: str,
                           onnx_nodes: list):
        # Since our representation do not consider the batch dimension we need to scale the axis by 1
        # when we pass to the onnx representation.
        temp_axis = current_node.axis + 1

        onnx_node = onnx.helper.make_node(
            'Flatten',
            inputs=[current_input],
            outputs=[current_output],
            axis=temp_axis
        )

        onnx_nodes.append(onnx_node)

    @staticmethod
    def __add_onnx_linear(current_node: nodes.FullyConnectedNode, current_input: str, current_output: str,
                        onnx_nodes: list, input_info: list, initializers: list):

        input_weight = current_node.identifier + "_weight"
        inputs = [current_input, input_weight]
        
        # Add weight
        input_info.append(onnx.helper.make_tensor_value_info(
            input_weight, TORCH_TO_ONNX_DTYPE[current_node.weight.dtype],
            [current_node.out_features, current_node.in_features]))
        initializers.append(onnx.numpy_helper.from_array(current_node.weight.detach().numpy().T, input_weight))
        
        # Add bias if present
        if current_node.has_bias:
            input_bias = current_node.identifier + "_bias"
            inputs.append(input_bias)
            input_info.append(onnx.helper.make_tensor_value_info(
                input_bias, TORCH_TO_ONNX_DTYPE[current_node.bias.dtype], [current_node.out_features]))
            initializers.append(onnx.numpy_helper.from_array(current_node.bias.detach().numpy(), input_bias))

        onnx_nodes.append(onnx.helper.make_node(
            'Gemm',
            inputs=inputs,
            outputs=[current_output],
            alpha=1.0,
            beta=1.0,
            transA=0,
            transB=0
        ))

    @staticmethod
    def __add_onnx_leakyrelu(current_node: nodes.LeakyReLUNode, current_input: str, current_output: str,
                             onnx_nodes: list):

        onnx_node = onnx.helper.make_node(
            'LeakyRelu',
            inputs=[current_input],
            outputs=[current_output],
            alpha=current_node.negative_slope
        )

        onnx_nodes.append(onnx_node)

    @staticmethod
    def __add_onnx_lrn(current_node: nodes.LRNNode, current_input: str, current_output: str,
                       onnx_nodes: list):

        onnx_node = onnx.helper.make_node(
            'LRN',
            inputs=[current_input],
            outputs=[current_output],
            alpha=current_node.alpha,
            beta=current_node.beta,
            bias=current_node.k,
            size=current_node.size
        )

        onnx_nodes.append(onnx_node)

    @staticmethod
    def __add_onnx_maxpool(current_node: nodes.MaxPoolNode, current_input: str, current_output: str,
                           onnx_nodes: list):
        # N.B. we do not support the attribute storage_order of ONNX
        # ONNX does not support the return_indices parameters
        onnx_node = onnx.helper.make_node(
            'MaxPool',
            inputs=[current_input],
            outputs=[current_output],
            ceil_mode=int(current_node.ceil_mode),
            dilations=current_node.dilation,
            kernel_shape=list(current_node.kernel_size),
            strides=list(current_node.stride),
            pads=list(current_node.padding)
        )

        onnx_nodes.append(onnx_node)

    @staticmethod
    def __add_onnx_relu(current_input: str, current_output: str, onnx_nodes: list):

        onnx_node = onnx.helper.make_node(
            'Relu',
            inputs=[current_input],
            outputs=[current_output],
        )

        onnx_nodes.append(onnx_node)

    @staticmethod
    def __add_onnx_reshape(current_node: nodes.ReshapeNode, current_input: str, current_output: str,
                           onnx_nodes: list, input_info: list, initializers: list):

        temp_shape = [1]
        for e in current_node.shape:
            temp_shape.append(e)
        shape_size = [len(current_node.shape)]
        input_shape = current_node.identifier + "_shape"

        shape_value_info = onnx.helper.make_tensor_value_info(input_shape, onnx.TensorProto.INT64,
                                                              shape_size)

        shape_tensor = onnx.numpy_helper.from_array(np.array(temp_shape), input_shape)

        onnx_node = onnx.helper.make_node(
            'Reshape',
            inputs=[current_input, input_shape],
            outputs=[current_output],
            allow_zero=int(current_node.allow_zero)
        )

        input_info.append(shape_value_info)
        initializers.append(shape_tensor)

        onnx_nodes.append(onnx_node)

    @staticmethod
    def __add_onnx_sigmoid(current_input: str, current_output: str, onnx_nodes: list):

        onnx_node = onnx.helper.make_node(
            'Sigmoid',
            inputs=[current_input],
            outputs=[current_output],
        )

        onnx_nodes.append(onnx_node)

    @staticmethod
    def __add_onnx_softmax(current_node: nodes.SoftMaxNode, current_input: str, current_output: str,
                           onnx_nodes: list):
        # Since our representation do not consider the batch dimension we need to scale the axis by 1
        # when we pass to the onnx representation.
        temp_axis = current_node.axis + 1
        onnx_node = onnx.helper.make_node(
            'Softmax',
            inputs=[current_input],
            outputs=[current_output],
            axis=temp_axis
        )

        onnx_nodes.append(onnx_node)

    @staticmethod
    def __add_onnx_sum(current_node: nodes.SumNode, current_inputs: list[str], current_output: str, onnx_nodes: list):
        """
        Add a Sum node to the ONNX graph.
        All input tensors must have the same shape.

        Parameters
        ----------
        current_node : nodes.SumNode
            The sum node to convert.
        current_inputs : list[str]
            List of input identifiers to be summed.
        current_output : str
            The output identifier.
        onnx_nodes : list
            The list to append the ONNX node to.
        """
        onnx_node = onnx.helper.make_node(
            'Sum',
            inputs=current_inputs,
            outputs=[current_output],
            name=current_node.identifier
        )
        onnx_nodes.append(onnx_node)

    @staticmethod
    def __add_onnx_tanh(current_input: str, current_output: str, onnx_nodes: list):

        onnx_node = onnx.helper.make_node(
            'Tanh',
            inputs=[current_input],
            outputs=[current_output],
        )

        onnx_nodes.append(onnx_node)

    @staticmethod
    def __add_onnx_transpose(current_node: nodes.TransposeNode, current_input: str, current_output: str,
                             onnx_nodes: list):
        # Since our representation do not consider the batch dimension we need to scale the perm by 1
        # and add the 0 dimension when we pass to the onnx representation.
        perm = [0]
        for p in current_node.perm:
            perm.append(p + 1)

        onnx_node = onnx.helper.make_node(
            'Transpose',
            inputs=[current_input],
            outputs=[current_output],
            perm=perm
        )

        onnx_nodes.append(onnx_node)

    @staticmethod
    def __add_onnx_unsqueeze(current_node: nodes.UnsqueezeNode, current_input: str, current_output: str,
                             onnx_nodes: list, input_info: list, initializers: list):

        axes_size = [len(current_node.axes)]
        input_axes = current_node.identifier + "_axes"

        axes_value_info = onnx.helper.make_tensor_value_info(input_axes, onnx.TensorProto.INT64,
                                                             axes_size)

        temp_axes = [e + 1 for e in current_node.axes]
        axes_tensor = onnx.numpy_helper.from_array(np.array(temp_axes), input_axes)

        onnx_node = onnx.helper.make_node(
            'Unsqueeze',
            inputs=[current_input, input_axes],
            outputs=[current_output]
        )

        input_info.append(axes_value_info)
        initializers.append(axes_tensor)

        onnx_nodes.append(onnx_node)

    def __add_node(self, current_node, current_input, current_inputs, current_output, onnx_nodes, input_info, initializers):
        """Export a single internal node to ONNX format."""
        # Create a mapping of node types to their handler methods
        node_handlers = {
            nodes.AveragePoolNode: lambda: self.__add_onnx_averagepool(current_node, current_input, current_output, onnx_nodes),
            nodes.BatchNormNode: lambda: self.__add_onnx_batchnorm(current_node, current_input, current_output, onnx_nodes, input_info, initializers),
            nodes.CELUNode: lambda: self.__add_onnx_celu(current_node, current_input, current_output, onnx_nodes),
            nodes.ConcatNode: lambda: self.__add_onnx_concat(current_node, current_inputs, current_output, onnx_nodes),
            nodes.ConvNode: lambda: self.__add_onnx_conv(current_node, current_input, current_output, onnx_nodes, input_info, initializers),
            nodes.DropoutNode: lambda: self.__add_onnx_dropout(current_node, current_input, current_output, onnx_nodes, input_info, initializers),
            nodes.ELUNode: lambda: self.__add_onnx_elu(current_node, current_input, current_output, onnx_nodes),
            nodes.FlattenNode: lambda: self.__add_onnx_flatten(current_node, current_input, current_output, onnx_nodes),
            nodes.FullyConnectedNode: lambda: self.__add_onnx_linear(current_node, current_input, current_output, onnx_nodes, input_info, initializers),
            nodes.LeakyReLUNode: lambda: self.__add_onnx_leakyrelu(current_node, current_input, current_output, onnx_nodes),
            nodes.LRNNode: lambda: self.__add_onnx_lrn(current_node, current_input, current_output, onnx_nodes),
            nodes.MaxPoolNode: lambda: self.__add_onnx_maxpool(current_node, current_input, current_output, onnx_nodes),
            nodes.ReLUNode: lambda: self.__add_onnx_relu(current_input, current_output, onnx_nodes),
            nodes.ReshapeNode: lambda: self.__add_onnx_reshape(current_node, current_input, current_output, onnx_nodes, input_info, initializers),
            nodes.SigmoidNode: lambda: self.__add_onnx_sigmoid(current_input, current_output, onnx_nodes),
            nodes.SoftMaxNode: lambda: self.__add_onnx_softmax(current_node, current_input, current_output, onnx_nodes),
            nodes.SumNode: lambda: self.__add_onnx_sum(current_node, current_inputs, current_output, onnx_nodes),
            nodes.TanhNode: lambda: self.__add_onnx_tanh(current_input, current_output, onnx_nodes),
            nodes.TransposeNode: lambda: self.__add_onnx_transpose(current_node, current_input, current_output, onnx_nodes),
            nodes.UnsqueezeNode: lambda: self.__add_onnx_unsqueeze(current_node, current_input, current_output, onnx_nodes, input_info, initializers),
        }
        
        node_type = type(current_node)
        if node_type not in node_handlers:
            raise NotImplementedError(f"Node type {node_type} not implemented during the export of acyclic networks")
        
        # Execute the handler for this node type
        node_handlers[node_type]()

    def __from_neural_network_sequential(self, network: networks.SequentialNetwork) -> ONNXNetwork:
        """
        Convert a sequential neural network to ONNX representation.
        
        Parameters
        ----------
        network : SequentialNetwork
            The sequential neural network to convert.
            
        Returns
        ----------
        ONNXNetwork
            The ONNX representation resulting from the conversion of the original network.
        """
        input_info = []
        output_info = []
        initializers = []
        onnx_nodes = []
        
        current_node = network.get_first_node()
        previous_output = network.get_input_id()
        
        while current_node is not None:
            current_input = previous_output
            current_inputs = [current_input]  # Sequential networks have single inputs
            current_output = current_node.identifier

            input_dim = [1]
            if isinstance(current_node.get_input_dim(), list):
                raise Exception('Sequential networks cannot have multiple input layers')

            for e in current_node.get_input_dim():
                input_dim.append(e)

            output_dim = [1]
            for e in current_node.out_dim:
                output_dim.append(e)

            input_value_info = onnx.helper.make_tensor_value_info(current_input, onnx.TensorProto.FLOAT,
                                                                input_dim)
            output_value_info = onnx.helper.make_tensor_value_info(current_output, onnx.TensorProto.FLOAT,
                                                                output_dim)

            input_info.append(input_value_info)
            output_info.append(output_value_info)

            self.__add_node(current_node, current_input, current_inputs, current_output, onnx_nodes, input_info, initializers)

            previous_output = current_output
            current_node = network.get_next_node(current_node)
        
        # Create ONNX graph and model
        onnx_graph = onnx.helper.make_graph(
            nodes=onnx_nodes,
            name=network.identifier,
            inputs=[input_info[0]],
            outputs=[output_info[-1]],
            initializer=initializers,
            value_info=input_info
        )

        onnx_network = onnx.helper.make_model(graph=onnx_graph)
        return ONNXNetwork(network.identifier, onnx_network)

    def __from_neural_network_acyclic(self, network: networks.AcyclicNetwork) -> ONNXNetwork:
        """
        Convert an acyclic neural network to ONNX representation.
        
        Parameters
        ----------
        network : AcyclicNetwork
            The acyclic neural network to convert.
            
        Returns
        ----------
        ONNXNetwork
            The ONNX representation resulting from the conversion of the original network.
        """
        input_info = []
        output_info = []
        initializers = []
        onnx_nodes = []
        
        child_depth = []
        current_depth = network.get_roots()
        can_treat_the_node = True
        visited = set()  # Using set because it don't take doublons, and is faster to verify the in condition
        
        while current_depth:
            for current_node in current_depth:
                node_parent = network.get_parents(current_node)
                for node in node_parent:
                    if node not in visited:  # If a parent of the node has not been added to onnx, then treat this node later
                        can_treat_the_node = False
                        if current_node not in child_depth:
                            child_depth.append(current_node)
                if current_node in visited:  # Avoid the same node to be added twice
                    can_treat_the_node = False
                
                # If all parents have been seen and the node has not been added: then treat this node
                if can_treat_the_node:
                    # Add input_ids
                    current_inputs = network.get_input_ids_by_node(current_node)
                    # Add parents
                    current_inputs += [input.identifier for input in network.get_parents(current_node)]
                    
                    # If it's not an add or concatenate
                    current_input = str(current_inputs[0])  # used only for single-input layers 
                    current_output = current_node.identifier

                    input_dim = [1]
                    for e in current_node.get_input_dim():  # in case e is a tuple
                        input_dim.extend(e if isinstance(e, tuple) else [e])

                    output_dim = [1]
                    for e in current_node.out_dim:  # idem
                        output_dim.extend(e if isinstance(e, tuple) else [e])

                    for input_name in current_inputs:
                        input_value_info = onnx.helper.make_tensor_value_info(str(input_name), onnx.TensorProto.FLOAT,
                                                                            input_dim)
                        if input_value_info not in input_info:
                            input_info.append(input_value_info)

                    output_value_info = onnx.helper.make_tensor_value_info(str(current_output), onnx.TensorProto.FLOAT,
                                                                        output_dim)
                    if output_value_info not in output_info:
                        output_info.append(output_value_info)

                    self.__add_node(current_node, current_input, current_inputs, current_output, onnx_nodes, input_info, initializers)

                    # Add the node to the visited set, and add its children to the queue
                    visited.add(current_node)
                    for child in network.get_children(current_node):
                        if child not in child_depth:
                            child_depth.append(child)
                else:  # We skipped this node, now we reset the can_treat_the_node condition
                    can_treat_the_node = True

            current_depth = child_depth
            child_depth = []
        
        # Create ONNX graph and model
        onnx_graph = onnx.helper.make_graph(
            nodes=onnx_nodes,
            name=network.identifier,
            inputs=[input_info[0]],
            outputs=[output_info[-1]],
            initializer=initializers,
            value_info=input_info
        )

        onnx_network = onnx.helper.make_model(graph=onnx_graph)
        return ONNXNetwork(network.identifier, onnx_network)

    def from_neural_network(self, network: networks.NeuralNetwork) -> ONNXNetwork:
        """
        Convert the neural network of interest to a ONNX representation.

        Parameters
        ----------
        network : NeuralNetwork
            The neural network to convert.

        Returns
        ----------
        ONNXNetwork
            The ONNX representation resulting from the conversion of the original network.

        """
        if isinstance(network, networks.SequentialNetwork):
            return self.__from_neural_network_sequential(network)
        elif isinstance(network, networks.AcyclicNetwork):
            return self.__from_neural_network_acyclic(network)
        else:
            raise NotImplementedError(f"Network type {type(network)} not supported")


    @staticmethod
    def __onnx_extract_input_shapes(alt_rep:ONNXNetwork, include_initializers=False):
        """
        Build a dict mapping each external input (and optionally initializer) 
        name to its shape as a tuple.

        Parameters
        ----------
        alt_rep : ONNXNetwork
            The ONNX model.
        include_initializers : bool
            If True, also include graph.initializer tensors.

        Returns
        -------
        dict[str, tuple[int|str|None]]
            Mapping input/initializer names -> shape tuple.
            Dimensions may be int, str (symbolic), or None (unknown).
        """
        model = alt_rep.onnx_network
        graph = model.graph

        def get_dims(value_info):
            dims = []
            for d in value_info.type.tensor_type.shape.dim:
                if d.HasField("dim_value"):
                    dims.append(int(d.dim_value))
                elif d.HasField("dim_param"):
                    dims.append(d.dim_param)   # symbolic like "N"
                else:
                    dims.append(None)          # unknown
            return tuple(dims)

        # Start with graph.input entries
        shape_dict = {vi.name: get_dims(vi) for vi in graph.input}

        # Optionally add initializers
        if include_initializers:
            for init in graph.initializer:
                shape_dict[init.name] = tuple(init.dims)

        else:
            # Exclude any inputs that are actually initializers
            initializer_names = {init.name for init in graph.initializer}
            for name in list(shape_dict.keys()):
                if name in initializer_names:
                    del shape_dict[name]

        return shape_dict

    @staticmethod
    def __onnx_extract_parameters(alt_rep:ONNXNetwork):
        '''
        Extract all the parameters from a ONNXNetwork.
        
        Parameters
        ----------
        alt_rep : ONNXNetwork
            The ONNX Representation to extract the parameters from.

        Returns
        ----------
        dict[str, np.ndarray]
            The parameters of each initializer of the network, the keys are the initializers'names.
        '''

        parameters = dict()

        for initializer in alt_rep.onnx_network.graph.initializer:
            parameters[initializer.name] = onnx.numpy_helper.to_array(initializer)
        return parameters

    @staticmethod
    def __build_shape_dict(alt_rep: ONNXNetwork):
        """
        Build a flat dict mapping every tensor name (model inputs, layer inputs/outputs,
        and initializers) to its inferred shape.

        Parameters
        ----------
        alt_rep : ONNXNetwork
            The ONNX model.

        Returns
        -------
        dict[str, tuple[int|str|None]]
            Mapping tensor_name -> shape tuple.
            Dimensions may be int, str (symbolic), or None (unknown).
        """
        model = alt_rep.onnx_network
        inferred = onnx.shape_inference.infer_shapes(model)
        graph = inferred.graph

        def get_value_info_shape(value_info):
            dims = []
            for d in value_info.type.tensor_type.shape.dim:
                if d.HasField("dim_value"):
                    dims.append(int(d.dim_value))
                elif d.HasField("dim_param"):
                    dims.append(d.dim_param)   # symbolic dim like "N"
                else:
                    dims.append(None)          # unknown
            return tuple(dims)

        shape_dict = {}

        # Model inputs, hidden tensors, model outputs
        for vi in list(graph.input) + list(graph.value_info) + list(graph.output):
            shape_dict[vi.name] = get_value_info_shape(vi)

        # Initializers (weights/biases)
        for init in graph.initializer:
            shape_dict[init.name] = tuple(init.dims)

        return shape_dict

    @staticmethod
    def __is_sequential_onnx(alt_rep: ONNXNetwork) -> bool:
        """
        Check whether the onnx network provided is sequential or not.
        Parameters
        ----------
        alt_rep : ONNXNetwork
            The ONNX Representation to check.
        Returns
        ----------
        bool
            True if the onnx network is sequential, False otherwise.
        """
        #Main assumption:
        #  if an output is input of more than one node, then the network is not sequential, and if there is more than one output then the network is not sequential.

        onnx_graph = alt_rep.onnx_network.graph

        inputs = list(ONNXConverter.__onnx_extract_input_shapes(alt_rep, False).keys())
        if len(inputs) > 1: 
            return False
        outputs = [x.name for x in onnx_graph.output]
        if len(outputs) > 1: 
            return False

        input_counter = {i:0 for i in inputs+outputs}
        for node in onnx_graph.node:
            for out in node.output:
                if out not in input_counter.keys():
                    input_counter[out] = 0
            for inp in node.input:
                if inp in input_counter.keys():
                    input_counter[inp] += 1
                    if input_counter[inp] > 1:
                        return False 
        return True

    @staticmethod
    def normalize_fc_layers(alt_rep: ONNXNetwork):
        """
        Normalize the ONNX representation by replacing all occurrences of MatMul + Add
        with a single Gemm node.
        Parameters
        ----------
        alt_rep : ONNXNetwork
            The ONNX Representation to normalize.
        Returns
        ----------
        ONNXNetwork
            The Neural Network resulting from the normalization.
        """
        model = alt_rep.onnx_network
        graph = model.graph
        new_nodes = []
        skip_nodes = set()
        removed_outputs = set()  # Track intermediate outputs that are removed
        
        # Output -> node lookup
        input_to_node = {inp: node for node in graph.node for inp in node.input}
        
        for node in graph.node:
            if node.op_type == "MatMul" and len(node.output) > 0:
                matmul_output = node.output[0]
                
                # Check if this MatMul output is used by an Add node
                if matmul_output in input_to_node:
                    next_node = input_to_node[matmul_output] # matmul output is input to a node
                    
                    if next_node.op_type == "Add" and len(next_node.input) == 2:
                        matmul_inputs = list(node.input)
                        add_inputs = list(next_node.input)
                        
                        # Find the bias input (the Add input that is not the MatMul output)
                        bias_input = None
                        for inp in add_inputs:
                            if inp != matmul_output:
                                bias_input = inp
                                break
                        
                        if bias_input is not None:
                            # Create Gemm node with correct output (use Add node's output)
                            gemm_node = onnx.helper.make_node(
                                "Gemm",
                                inputs=[matmul_inputs[0], matmul_inputs[1], bias_input],
                                outputs=next_node.output,  # Use Add node's output, not MatMul's
                                name=f"{node.name}_gemm" if node.name else f"{next_node.name}_gemm",
                                alpha=1.0,  # Default values for Gemm
                                beta=1.0,
                                transA=0,
                                transB=0
                            )
                            
                            new_nodes.append(gemm_node)
                            skip_nodes.update({node.name, next_node.name})
                            removed_outputs.add(matmul_output)  # Mark intermediate output for removal
                            continue
            
            # Add node if it's not being skipped
            if node.name not in skip_nodes:
                new_nodes.append(node)
        
        # Filter out value_info entries for removed intermediate outputs
        filtered_value_info = []
        for value_info in graph.value_info:
            if value_info.name not in removed_outputs:
                filtered_value_info.append(value_info)
        
        # Create new graph with filtered value_info
        new_graph = onnx.helper.make_graph(
            new_nodes,
            graph.name,
            graph.input,
            graph.output,
            graph.initializer,
            # value_info=filtered_value_info this is creating problems and it is not mandatory according to the function documentation
        )
        
        new_model = onnx.helper.make_model(new_graph, producer_name="normalize_fc_layers")
            
        # Copy model metadata
        new_model.ir_version = model.ir_version
        new_model.opset_import.extend(model.opset_import)
        
        return ONNXNetwork(alt_rep.identifier, new_model)


    @staticmethod
    def __process_add(node, in_dim, parameters):
        """Process Add node."""
        return nodes.SumNode(node.output[0],in_dims=in_dim)
    
    @staticmethod
    def __process_average_pool(node, in_dim, parameters):
        """Process AveragePool node."""
        # TODO: at present we do not support auto_pad.
        ceil_mode = False
        count_include_pad = False
        padding = tuple(np.zeros(2 * len(in_dim[1:]), dtype=np.intc))
        stride = tuple(np.ones(len(in_dim[1:]), dtype=np.intc))
        kernel_shape = None

        for att in node.attribute:
            if att.name == 'ceil_mode':
                ceil_mode = bool(att.i)
            elif att.name == 'count_include_pad':
                count_include_pad = bool(att.i)
            elif att.name == 'kernel_shape':
                kernel_shape = tuple(att.ints)
            elif att.name == 'pads':
                padding = tuple(att.ints)
            elif att.name == 'strides':
                stride = tuple(att.ints)

        return nodes.AveragePoolNode(node.output[0], in_dim, kernel_shape, stride,
                                padding, ceil_mode, count_include_pad)
    @staticmethod
    def __process_batch_norm(node, in_dim, parameters):
        """Process BatchNormalization node."""
        weight = Tensor(parameters[node.input[1]])
        bias = Tensor(parameters[node.input[2]])
        running_mean = Tensor(parameters[node.input[3]])
        running_var = Tensor(parameters[node.input[4]])

        eps = 1e-05
        momentum = 0.9
        for att in node.attribute:
            if att.name == 'epsilon':
                eps = att.f
            elif att.name == 'momentum':
                momentum = att.f

        return nodes.BatchNormNode(node.output[0], in_dim, weight,
                                bias, running_mean, running_var, eps, momentum)

    @staticmethod
    def __process_celu(node, in_dim, parameters):
        """Process CELU node."""
        alpha = 1.0
        for att in node.attribute:
            if att.name == 'alpha':
                alpha = att.f
        return nodes.CELUNode(node.output[0], in_dim, alpha)

    @staticmethod
    def __process_concat(node, in_dim, parameters):
        """Process Concat node."""
        axis=-1
        for att in node.attribute:
            if att.name == 'axis':
                axis = att.i
        if axis > 0:
            axis = axis - 1
        return nodes.ConcatNode(node.output[0], in_dim, axis)

    @staticmethod
    def __process_constant(node, in_dim, parameters):
        """Process a constant node..."""
        for attr in node.attribute:
            if attr.name == "value":
                const_array = onnx.numpy_helper.to_array(attr.t)
                parameters[node.output[0]] = const_array
        return None

    @staticmethod
    def __process_conv(node, in_dim, parameters):
        """Process Conv node."""
        weight = Tensor(parameters[node.input[1]])
        has_bias = len(node.input) > 2
        bias = Tensor(parameters[node.input[2]]) if has_bias else None
        
        out_channels = weight.shape[0]
        groups = 1
        dilation = tuple(np.ones(len(in_dim[1:]), dtype=np.intc))
        padding = tuple(np.zeros(2 * len(in_dim[1:]), dtype=np.intc))
        stride = tuple(np.ones(len(in_dim[1:]), dtype=np.intc))
        kernel_shape = None

        for att in node.attribute:
            if att.name == 'dilations':
                dilation = tuple(att.ints)
            elif att.name == 'groups':
                groups = att.i
            elif att.name == 'kernel_shape':
                kernel_shape = tuple(att.ints)
            elif att.name == 'pads':
                padding = tuple(att.ints)
            elif att.name == 'strides':
                stride = tuple(att.ints)
        
        if kernel_shape is None:
            kernel_shape = tuple(weight.shape[2:])

        return nodes.ConvNode(node.output[0], in_dim, out_channels, kernel_shape,
                            stride, padding, dilation, groups, has_bias, bias, weight)

    @staticmethod
    def __process_dropout(node, in_dim, parameters):
        """Process Dropout node."""
        # The default value of the ratio in onnx is 0.5
        # we need to take it into account because it is optional
        ratio = 0.5
        if len(node.input) > 1:
            ratio = Tensor(parameters[node.input[1]])
        return nodes.DropoutNode(node.output[0], in_dim, ratio)

    @staticmethod
    def __process_elu(node, in_dim, parameters):
        """Process ELU node."""
        alpha = 1.0
        for att in node.attribute:
            if att.name == 'alpha':
                alpha = att.f
        return nodes.ELUNode(node.output[0], in_dim, alpha)

    @staticmethod
    def __process_flatten(node, in_dim, parameters):
        """Process Flatten node."""
        axis = 0
        for att in node.attribute:
            if att.name == 'axis':
                axis = att.i - 1
        return nodes.FlattenNode(node.output[0], in_dim, axis)

    @staticmethod
    def __process_gemm(node, in_dim, parameters):
        """Process Gemm node."""
        weight = Tensor(parameters[node.input[1]])
        for att in node.attribute:
            if att.name == 'transB' and att.i == 0:
                weight = Tensor(parameters[node.input[1]].T)

        has_bias = len(node.input) > 2
        bias = Tensor(parameters[node.input[2]]) if has_bias else None
        out_features = weight.shape[0]
        
        return nodes.FullyConnectedNode(
            node.output[0], in_dim, out_features, weight, bias, has_bias
        )

    @staticmethod
    def __process_leaky_relu(node, in_dim, parameters):
        """Process LeakyReLU node."""
        negative_slope = 1.0
        for att in node.attribute:
            if att.name == 'alpha':
                negative_slope = att.f
        return nodes.LeakyReLUNode(node.output[0], in_dim, negative_slope)

    @staticmethod
    def __process_lrn(node, in_dim, parameters):
        """Process LRN node."""
        alpha = 0.0001
        beta = 0.75
        k = 1.0

        for att in node.attribute:
            if att.name == 'alpha':
                alpha = att.f
            elif att.name == 'beta':
                beta = att.f
            elif att.name == 'bias':
                k = att.f
            elif att.name == 'size':
                size = att.i

        return nodes.LRNNode(node.output[0], in_dim, size, alpha, beta, k)

    @staticmethod
    def __process_matmul(node, in_dim, parameters):
        """Process MatMul node."""
        if node.input[0] in parameters.keys():
            weight = parameters[node.input[0]]
        else:
            weight = parameters[node.input[1]].T

        weight = Tensor(weight)
        out_features = weight.shape[0]
        return nodes.FullyConnectedNode(node.output[0], in_dim, out_features, weight, None, False)

    @staticmethod
    def __process_max_pool(node, in_dim, parameters):
        """Process MaxPool node."""
        ceil_mode = False
        dilation = tuple(np.ones(len(in_dim[1:]), dtype=np.intc))
        padding = tuple(np.zeros(2 * len(in_dim[1:]), dtype=np.intc))
        stride = tuple(np.ones(len(in_dim[1:]), dtype=np.intc))
        kernel_shape = None

        for att in node.attribute:
            if att.name == 'ceil_mode':
                ceil_mode = bool(att.i)
            elif att.name == 'dilations':
                dilation = tuple(att.ints)
            elif att.name == 'kernel_shape':
                kernel_shape = tuple(att.ints)
            elif att.name == 'pads':
                padding = tuple(att.ints)
            elif att.name == 'strides':
                stride = tuple(att.ints)

        return nodes.MaxPoolNode(node.output[0], in_dim, kernel_shape, stride, padding,
                            dilation, ceil_mode)

    @staticmethod
    def __process_relu(node, in_dim, parameters):
        """Process ReLU node."""
        return nodes.ReLUNode(node.output[0], in_dim)

    @staticmethod
    def __process_reshape(node, in_dim, parameters):
        """Process Reshape node."""
        shape = tuple(parameters[node.input[1]])
        shape = shape[1:]
        allow_zero = 0
        for att in node.attribute:
            if att.name == 'allowzero':
                allow_zero = att.i

        return nodes.ReshapeNode(node.output[0], in_dim, shape, allow_zero)

    @staticmethod
    def __process_sigmoid(node, in_dim, parameters):
        """Process Sigmoid node."""
        return nodes.SigmoidNode(node.output[0], in_dim)

    @staticmethod
    def __process_skip_node(node, in_dim, parameters):
        """Irrelevant node."""
        return None

    @staticmethod
    def __process_softmax(node, in_dim, parameters):
        """Process Softmax node."""
        axis = -1
        for att in node.attribute:
            if att.name == 'axis':
                axis = att.i - 1

        return nodes.SoftMaxNode(node.output[0], in_dim, axis)

    @staticmethod
    def __process_tanh(node, in_dim, parameters):
        """Process Tanh node."""
        return nodes.TanhNode(node.output[0], in_dim)

    @staticmethod
    def __process_transpose(node, in_dim, parameters):
        """Process Transpose node."""
        perm = None
        for att in node.attribute:
            if att.name == 'perm':
                if len(att.ints) > len(in_dim):
                    perm = [att.ints[k] - 1 for k in range(1, len(att.ints))]
                else:
                    perm = att.ints

        return nodes.TransposeNode(node.output[0], in_dim, perm)

    @staticmethod
    def __process_unsqueeze(node, in_dim, parameters):
        """Process Unsqueeze node."""
        temp_axes = tuple(parameters[node.input[1]])
        axes = tuple([e - 1 for e in temp_axes])
        return nodes.UnsqueezeNode(node.output[0], in_dim, axes)
    
    def __process_node(self, node, in_dim, parameters):
        """Process a single ONNX node and return the corresponding internal node."""
        
        # Create a mapping of node types to their handler methods
        node_handlers = {
        "Add": self.__process_add,
        "AveragePool": self.__process_average_pool,
        "BatchNormalization": self.__process_batch_norm,
        "Celu": self.__process_celu,
        "Concat": self.__process_concat,
        "Constant": self.__process_constant,
        "Conv": self.__process_conv,
        "Div": self.__process_skip_node,
        "Dropout": self.__process_dropout,
        "Elu": self.__process_elu,
        "Flatten": self.__process_flatten,
        "Gemm": self.__process_gemm,
        "LeakyRelu": self.__process_leaky_relu,
        "LRN": self.__process_lrn,
        "MatMul": self.__process_matmul,
        "MaxPool": self.__process_max_pool,
        "Relu": self.__process_relu,
        "Reshape": self.__process_reshape,
        "Sigmoid": self.__process_sigmoid,
        "Softmax": self.__process_softmax,
        "Sub": self.__process_skip_node,
        "Sum": self.__process_add,
        "Tanh": self.__process_tanh,
        "Transpose": self.__process_transpose,
        "Unsqueeze": self.__process_unsqueeze,
        }
        
        if node.op_type not in node_handlers:
            raise NotImplementedError(f"Node type {node.op_type} not implemented during the import of acyclic networks")
        
        return node_handlers[node.op_type](node, in_dim, parameters)


    def __to_neural_network_squential(self, alt_rep: ONNXNetwork) -> networks.SequentialNetwork:
        """
        Convert the ONNX representation of interest to the internal one assuming the network to be a squential neural network.

        Parameters
        ----------
        alt_rep : ONNXNetwork
            The ONNX Representation to convert.

        Returns
        ----------
        SequentialNetwork
            The Sequential Neural Network resulting from the conversion of ONNX Representation.

        """

        identifier = alt_rep.identifier
        tmp = alt_rep.onnx_network.graph.input[0].name
        network = networks.SequentialNetwork(identifier, tmp)
        print(f"input id: {alt_rep.onnx_network.graph.input[0].name}")

        parameters = {}

        for initializer in alt_rep.onnx_network.graph.initializer:
            parameters[initializer.name] = onnx.numpy_helper.to_array(initializer)

        shape_info = {}
        for i in alt_rep.onnx_network.graph.input:
            shape = []
            for dim in i.type.tensor_type.shape.dim:
                shape.append(dim.dim_value)
            shape_info[i.name] = shape

        node_index = 1
        in_dim = tuple(shape_info[alt_rep.onnx_network.graph.input[0].name][1:])
        if in_dim == ():
            in_dim = tuple(shape_info[alt_rep.onnx_network.graph.input[0].name])

        temp_fc = None
        matmul_found = False

        for node in alt_rep.onnx_network.graph.node:
            """ This part of code handles the case when there is a MatMul + Add for a linear transformation """
            if matmul_found:
                if node.op_type == "Add":
                    # We assume that the bias is always the second element of node.input
                    bias = Tensor(parameters[node.input[1]])
                    network.append_node(nodes.FullyConnectedNode(temp_fc.identifier, temp_fc.get_input_dim(),
                                                                 temp_fc.out_features, temp_fc.weight, bias))
                    matmul_found = False
                    temp_fc = None
                    node_index += 1
                    in_dim = network.get_last_node().out_dim
                    continue

                else:
                    network.append_node(nodes.FullyConnectedNode(temp_fc.identifier, temp_fc.get_input_dim(),
                                                                 temp_fc.out_features, temp_fc.weight, has_bias=False))
                    matmul_found = False
                    temp_fc = None
                    node_index += 1
                    in_dim = network.get_last_node().out_dim

            if node.op_type == "MatMul":
                # If the weight is the second parameter we need to transpose it
                if node.input[0] in parameters.keys():
                    weight = parameters[node.input[0]]
                else:
                    weight = parameters[node.input[1]].T

                weight = Tensor(weight)

                out_features = weight.shape[0]
                temp_fc = nodes.FullyConnectedNode(node.output[0], in_dim, out_features, weight, has_bias=False)
                matmul_found = True

                continue

            elif node.op_type == 'Sub':
                """ This node is not relevant for verification and should not appear at all in benchmarks """
                continue

            elif node.op_type == 'Constant':
                """ This node is not relevant for verification and should not appear at all in benchmarks """

                for attr in node.attribute:
                    if attr.name == "value":
                        const_array = onnx.numpy_helper.to_array(attr.t)
                        parameters[node.output[0]] = const_array
                continue

            elif node.op_type == 'Div':
                """ This node is not relevant for verification and should not appear at all in benchmarks """
                continue

            elif node.op_type == "Relu":
                # We assume that the real input of the node is always the first element of node.input
                # and the first element of the shape is the batch placeholder
                network.append_node(nodes.ReLUNode(node.output[0], in_dim))

            elif node.op_type == "Elu":
                alpha = 1.0
                for att in node.attribute:
                    if att.name == 'alpha':
                        alpha = att.f
                network.append_node(nodes.ELUNode(node.output[0], in_dim, alpha))

            elif node.op_type == "LeakyRelu":
                negative_slope = 1.0
                for att in node.attribute:
                    if att.name == 'alpha':
                        negative_slope = att.f
                network.append_node(nodes.LeakyReLUNode(node.output[0], in_dim, negative_slope))

            elif node.op_type == "Celu":
                alpha = 1.0
                for att in node.attribute:
                    if att.name == 'alpha':
                        alpha = att.f
                network.append_node(nodes.CELUNode(node.output[0], in_dim, alpha))

            elif node.op_type == "Sigmoid":
                network.append_node(nodes.SigmoidNode(node.output[0], in_dim))

            elif node.op_type == "Tanh":
                network.append_node(nodes.TanhNode(node.output[0], in_dim))

            elif node.op_type == "Gemm":
                # We assume that the weight tensor is always the second element of node.input and the bias tensor
                # is always the third.
                # N.B: We do not support the attributes transA and transB,
                # therefore we need to transpose the weight vector.
                # TODO: Can we support transA and transB in some way?
                weight = Tensor(parameters[node.input[1]])
                for att in node.attribute:
                    if att.name == 'transB' and att.i == 0:
                        weight = Tensor(parameters[node.input[1]].T)

                if len(node.input) <= 2:
                    has_bias = False
                    bias = None
                else:
                    has_bias = True
                    bias = Tensor(parameters[node.input[2]])

                out_features = weight.shape[0]
                network.append_node(nodes.FullyConnectedNode(node.output[0], in_dim,
                                                             out_features, weight, bias, has_bias))
            elif node.op_type == "BatchNormalization":
                # We assume that the real input is always the first element of node.input, the weight tensor
                # is always the second, the bias tensor is always the third, the running_mean always the fourth
                # and the running_var always the fifth.

                weight = Tensor(parameters[node.input[1]])
                bias = Tensor(parameters[node.input[2]])
                running_mean = Tensor(parameters[node.input[3]])
                running_var = Tensor(parameters[node.input[4]])

                eps = 1e-05
                momentum = 0.9
                for att in node.attribute:

                    if att.name == 'epsilon':
                        eps = att.f
                    elif att.name == 'momentum':
                        momentum = att.f

                network.append_node(nodes.BatchNormNode(node.output[0], in_dim, weight,
                                                        bias, running_mean, running_var, eps, momentum))

            elif node.op_type == "Conv":
                # We assume that the real input is always the first element of node.input, the weight tensor
                # is always the second and the bias tensor is always the third.

                weight = Tensor(parameters[node.input[1]])
                if len(node.input) <= 2:
                    has_bias = False
                    bias = None
                else:
                    has_bias = True
                    bias = Tensor(parameters[node.input[2]])

                out_channels = weight.shape[0]

                # TODO: at present we do not support auto_pad.
                groups = 1
                # We need to exclude the first axis (channels) from the following quantities.
                dilation = tuple(torch.ones(len(in_dim[1:])))
                padding = tuple(torch.zeros(2 * len(in_dim[1:])))
                stride = tuple(torch.ones(len(in_dim[1:])))
                kernel_shape = None

                for att in node.attribute:
                    if att.name == 'dilations':
                        dilation = tuple(att.ints)
                    elif att.name == 'groups':
                        groups = att.i
                    elif att.name == 'kernel_shape':
                        kernel_shape = tuple(att.ints)
                    elif att.name == 'pads':
                        padding = tuple(att.ints)
                    elif att.name == 'strides':
                        stride = tuple(att.ints)
                
                if kernel_shape is None:
                    kernel_shape = tuple(weight.shape[2:])

                network.append_node(nodes.ConvNode(node.output[0], in_dim, out_channels, kernel_shape,
                                                   stride, padding, dilation, groups, has_bias, bias, weight))

            elif node.op_type == "AveragePool":
                # TODO: at present we do not support auto_pad.
                ceil_mode = False
                count_include_pad = False
                padding = tuple(torch.zeros(2 * len(in_dim[1:])))
                stride = tuple(torch.ones(len(in_dim[1:])))
                kernel_shape = None

                for att in node.attribute:
                    if att.name == 'ceil_mode':
                        ceil_mode = bool(att.i)
                    elif att.name == 'count_include_pad':
                        count_include_pad = bool(att.i)
                    elif att.name == 'kernel_shape':
                        kernel_shape = tuple(att.ints)
                    elif att.name == 'pads':
                        padding = tuple(att.ints)
                    elif att.name == 'strides':
                        stride = tuple(att.ints)

                network.append_node(nodes.AveragePoolNode(node.output[0], in_dim, kernel_shape, stride,
                                                          padding, ceil_mode, count_include_pad))

            elif node.op_type == "MaxPool":
                ceil_mode = False
                dilation = tuple(torch.ones(len(in_dim[1:])))
                padding = tuple(torch.zeros(2 * len(in_dim[1:])))
                stride = tuple(torch.ones(len(in_dim[1:])))
                kernel_shape = None

                for att in node.attribute:
                    if att.name == 'ceil_mode':
                        ceil_mode = bool(att.i)
                    elif att.name == 'dilations':
                        dilation = tuple(att.ints)
                    elif att.name == 'kernel_shape':
                        kernel_shape = tuple(att.ints)
                    elif att.name == 'pads':
                        padding = tuple(att.ints)
                    elif att.name == 'strides':
                        stride = tuple(att.ints)

                network.append_node(nodes.MaxPoolNode(node.output[0], in_dim, kernel_shape, stride, padding,
                                                      dilation, ceil_mode))

            elif node.op_type == "LRN":
                alpha = 0.0001
                beta = 0.75
                k = 1.0
                size = 0

                for att in node.attribute:
                    if att.name == 'alpha':
                        alpha = att.f
                    elif att.name == 'beta':
                        beta = att.f
                    elif att.name == 'bias':
                        k = att.f
                    elif att.name == 'size':
                        size = att.i

                network.append_node(nodes.LRNNode(node.output[0], in_dim, size, alpha, beta, k))

            elif node.op_type == "Softmax":
                # Since the ONNX representation consider the batch dimension we need to scale the axis by 1
                # when we pass to our representation.
                axis = -1
                for att in node.attribute:
                    if att.name == 'axis':
                        axis = att.i - 1
                network.append_node(nodes.SoftMaxNode(node.output[0], in_dim, axis))

            elif node.op_type == "Unsqueeze":
                temp_axes = tuple(parameters[node.input[1]])
                # Since our representation do not consider the batch dimension we need to scale all the axes
                # by 1 when we pass to the onnx representation.
                axes = tuple([e - 1 for e in temp_axes])
                network.append_node(nodes.UnsqueezeNode(node.output[0], in_dim, axes))

            elif node.op_type == "Reshape":
                shape = tuple(parameters[node.input[1]])
                # We need to eliminate the first dimension corresponding to the batch dimension
                shape = shape[1:]
                allow_zero = 0
                for att in node.attribute:
                    if att.name == 'allowzero':
                        allow_zero = att.i
                network.append_node(nodes.ReshapeNode(node.output[0], in_dim, shape, allow_zero))

            elif node.op_type == "Flatten":
                # We need to scale the axis value since our representation does not have the batch dimension
                axis = 0
                for att in node.attribute:
                    if att.name == 'axis':
                        axis = att.i - 1
                network.append_node(nodes.FlattenNode(node.output[0], in_dim, axis))

            elif node.op_type == "Dropout":
                # The default value of the ratio in onnx is 0.5
                # we need to take it into account because it is optional
                ratio = 0.5
                if len(node.input) > 1:
                    ratio = Tensor(parameters[node.input[1]])
                network.append_node(nodes.DropoutNode(node.output[0], in_dim, ratio))

            elif node.op_type == "Transpose":
                perm = None
                for att in node.attribute:
                    if att.name == 'perm':
                        # Must manage batch dimension
                        if len(att.ints) > len(in_dim):
                            perm = [att.ints[k] - 1 for k in range(1, len(att.ints))]
                        else:
                            perm = att.ints
                network.append_node(nodes.TransposeNode(node.output[0], in_dim, perm))

            else:
                raise NotImplementedError(f"Node type {node.op_type} not supported in the import of sequential networks")

            node_index += 1
            in_dim = network.get_last_node().out_dim
            # print(f"node {node_index} added, in_dim for next node is {in_dim}")

        return network

    def __to_neural_network_resnet(self, alt_rep: ONNXNetwork) -> networks.AcyclicNetwork: 
        """
        Convert the ONNX representation of interest to the internal one.
        It assumes the network to have an acyclic architectures (ResNet).
        This method should work also for sequential networks, but for efficiency purpose it is better to call the to_neural_network_sequential method.

        Parameters
        ----------
        alt_rep : ONNXNetwork
            The ONNX Representation to convert.

        Returns
        ----------
        AcyclicNetwork
            The Acyclic Neural Network resulting from the conversion of ONNX Representation.
        """

        alt_rep = self.normalize_fc_layers(alt_rep)
        # Extract parameters from ONNX initializers i.e. actual values of the initilizers
        parameters = self.__onnx_extract_parameters(alt_rep)
        shapes = self.__build_shape_dict(alt_rep)

        # Tracking dictionaries for acyclic network structure
        onnx_to_internal = {}

        identifier = alt_rep.identifier

        ##### First phase: get the network structure and create the singular nodes - internal representation
        onnx_graph = alt_rep.onnx_network.graph
        onnx_nodes = {}

        # Collect initializer names so we can filter them out
        initializer_names = {init.name for init in onnx_graph.initializer}

        # Build the dictionary
        for node in onnx_graph.node:
            filtered_inputs = {i for i in node.input if i not in initializer_names and i != ""}
            onnx_nodes[node.output[0]] = {
                "inputs": filtered_inputs,         # set of input tensor names (excluding weights/biases)
                "outputs": set(node.output),       # set of output tensor names
                "children": set(),                 # nodes consuming this node’s outputs
                "parents": set()                   # nodes producing this node’s inputs
            }

        # Fill children and parents
        node_names = list(onnx_nodes.keys())
        for n1 in node_names:
            for n1_out in onnx_nodes[n1]["outputs"]:
                for n2 in node_names:
                    if n1_out in onnx_nodes[n2]["inputs"]:
                        onnx_nodes[n2]["parents"].add(n1)
                        onnx_nodes[n1]["children"].add(n2)

        # TODO: extend to multi-input
        # Add network_input as possibile parents
        # Dimension of the input (Assuming only one input)
        net_input_name = alt_rep.onnx_network.graph.input[0].name
        network_input_ids = [net_input_name]  # Use the actual input tensor name from the graph

        # Drop batch dimension if present, otherwise keep full shape
        in_dim_network = tuple(shapes[net_input_name][1:])
        if in_dim_network == ():
            in_dim_network = tuple(shapes[net_input_name])
        in_dim_network = [in_dim_network]
        
        node_order = []

        for n in onnx_graph.node:
            identifier_of_node = n.output[0]
            if identifier_of_node not in onnx_nodes:
                continue

            if identifier_of_node in list(onnx_to_internal.keys()):
                continue

            if all(parent in onnx_to_internal for parent in onnx_nodes[identifier_of_node]['parents']):
                #TODO: this piece of code assumes only one input
                in_dims = [onnx_to_internal[p].out_dim if p in onnx_to_internal.keys() else in_dim_network[0] for p in onnx_nodes[identifier_of_node]['inputs']]

                if len(in_dims) == 1:
                    in_dims = in_dims[0] # for compability reasons with sequential networks

                internal_representation_node = self.__process_node(n, in_dims, parameters)
                onnx_to_internal[identifier_of_node] = internal_representation_node

                # If the layer has been skipped, rewire graph
                if not internal_representation_node:
                    # Rewire children
                    for child in list(onnx_nodes[identifier_of_node]['children']):
                        onnx_nodes[child]['parents'].discard(identifier_of_node)
                        onnx_nodes[child]['parents'].update(onnx_nodes[identifier_of_node]['parents'])
                        # Replace child's inputs: drop this node’s outputs, add this node’s inputs
                        onnx_nodes[child]['inputs'].difference_update(onnx_nodes[identifier_of_node]['outputs'])
                        onnx_nodes[child]['inputs'].update(onnx_nodes[identifier_of_node]['inputs'])

                    # Rewire parents
                    for parent in list(onnx_nodes[identifier_of_node]['parents']):
                        onnx_nodes[parent]['children'].discard(identifier_of_node)
                        onnx_nodes[parent]['children'].update(onnx_nodes[identifier_of_node]['children'])
                        # Replace parent's outputs: drop this node’s outputs, add child’s outputs
                        onnx_nodes[parent]['outputs'].difference_update(onnx_nodes[identifier_of_node]['outputs'])
                        for child in onnx_nodes[identifier_of_node]['children']:
                            onnx_nodes[parent]['outputs'].update(onnx_nodes[child]['outputs'])
                else:
                    node_order.append(identifier_of_node)
            else:
                print(f'Waring: I cannot compute {identifier_of_node} following the onnx DAG')
                # still_nodes_to_convert = True

        #### Second phase: link the nodes and build the actual network USING ONLY THE PARENTS AND CHILDREN OPTION OF THE DICTIONARY     
        network = networks.AcyclicNetwork(identifier, network_input_ids)#networks.AcyclicNetwork(identifier, tmp)
    
        for name in node_order:
            internal_representation = onnx_to_internal[name]
            parents = [onnx_to_internal[p] for p in onnx_nodes[name]['parents'] if p in onnx_to_internal.keys()]
            input_ids = [x for x in onnx_nodes[name]['inputs'] if x in network_input_ids]
            children = None# Not using right now

            network.add_node(internal_representation, parents, children, input_ids)

        return network
    
    def to_neural_network(self, alt_rep:ONNXNetwork) -> networks.NeuralNetwork:
        internal_representation = None
        
        if self.__is_sequential_onnx(alt_rep):
            internal_representation = self.__to_neural_network_squential(alt_rep)
        else:
            internal_representation = self.__to_neural_network_resnet(alt_rep)

        if not internal_representation:
            raise RuntimeError('Onnx to internal representation parsing have failed')
        
        return internal_representation