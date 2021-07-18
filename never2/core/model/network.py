class NetworkNode:
    """
    This class describes a network node block available for the user, with inputs,
    parameters and a description.

    Attributes
    ----------
    name : str
        Name of the block.
    class_name : str
        Name of the class of the block.
    input : dict
        Dictionary of the inputs taken by the node, connecting for each
        input its name to a dictionary of parameters such as type, default
        value, description.
    param : dict
        Dictionary of the parameters of the block, connecting for each
        parameter its name to a dictionary of parameters such as type, default
        value, description.
    output : dict
        Dictionary of the outputs of the block, , connecting for each
        output its name to a dictionary of parameters such as type, default
        value, description.
    descr : str
        Description of the operation done by the node.

    """

    def __init__(self, name: str, class_name: str, input: dict, param: dict, output: dict, descr: str):
        self.name = name
        self.class_name = class_name
        self.input = input
        self.param = param
        self.output = output
        self.descr = descr
