import json

import numpy as np
from PyQt5.QtCore import QRectF, QLineF, QPointF
from pynever.tensor import Tensor


def truncate(f: float, n: int) -> str:
    """
    Truncates/pads a float f to n decimal places without rounding

    """

    s = '{}'.format(f)
    if 'e' in s or 'E' in s:
        return '{0:.{1}f}'.format(f, n)
    i, p, d = s.partition('.')
    return '.'.join([i, (d + '0' * n)[:n]])


def get_sides_of(rect: QRectF):
    """
    This method returns the sides of a rect as a dictionary.
    Parameters
    ----------
    rect : QRectF
        The rect to inspect.
    Returns
    ----------
    dict
        A container of the sides represented as QLineF
        objects and their position as a key.

    """

    return {"top": QLineF(rect.topLeft(), rect.topRight()),
            "right": QLineF(rect.topRight(), rect.bottomRight()),
            "bottom": QLineF(rect.bottomLeft(), rect.bottomRight()),
            "left": QLineF(rect.bottomLeft(), rect.topLeft())}


def get_midpoint(label: str, side: QLineF) -> (QPointF, QPointF):
    """
    Procedure to compute the midpoint of a rectangle side.

    Parameters
    ----------
    label : str
        The side label ("top", "right", "bottom", "left")
    side : QLineF
        The line representing the side.

    Returns
    ----------
    tuple
        The two coordinates of the mid-point.

    """

    mid_x = (side.x1() + side.x2()) / 2
    mid_y = (side.y1() + side.y2()) / 2

    # Add a margin depending on the side
    if label == "top":
        mid_y += 4
    elif label == "right":
        mid_x -= 4
    elif label == "bottom":
        mid_y -= 4
    elif label == "left":
        mid_x += 4

    return mid_x, mid_y


def create_variables_from(v_name: str, v_dim: tuple) -> list:
    """
    This method creates a list of variables describing
    the tuple v_dim with the name v_name.

    Parameters
    ----------
    v_name : str
        The variable main name.
    v_dim : tuple
        The variable shape.

    Returns
    ----------
    list
        The list of string variables.

    """

    temp_list = []
    ped_list = []
    var_list = []

    # Add underscore
    v_name += '_'

    for k in v_dim:
        if len(temp_list) == 0:
            for i in range(k):
                temp_list.append(str(i))
        else:
            for i in range(k):
                for p in temp_list:
                    p = f"{p}-{i}"
                    ped_list.append(p)
            temp_list = ped_list
            ped_list = []

    for p in temp_list:
        var_list.append(f"{v_name}{p}")

    return var_list


def text_to_tensor(text: str) -> Tensor:
    """
    This method takes a string in format "n,m,l" with n, m, l
    are integers and converts it into a Tensor with the
    given dimensions.

    Parameters
    ----------
    text : str
        Input string to convert.
    Returns
    ----------
    Tensor
        The converted tensor.

    """

    dims = ()
    num = 0

    for c in text:
        if '0' <= c <= '9':
            num = (num * 10) + int(c)
        else:
            dims += (num,)
            num = 0
    dims += (num,)

    return Tensor(shape=dims, buffer=np.random.normal(size=dims))


def text_to_tensor_set(text: str) -> tuple:
    """
    This method takes a string in format "(n,m,l), (n,m,l), ..."
    where n, m, l are integers and converts it into a tuple containing
    the set of Tensors with the given dimensions.

    Parameters
    ----------
    text: str
        Input string to convert.
    Returns
    ----------
    tuple
        The converted tensor set.

    """

    tensors = tuple()
    temp = tuple()

    for token in text.split(", "):
        num = int(token.replace("(", "").replace(")", ""))
        temp += (num,)
        if ")" in token:
            tensors += (Tensor(shape=temp, buffer=np.random.normal(size=temp)),)

    return tensors


def read_json(path: str) -> dict:
    """
    This method loads the content of a JSON file
    located at the 'path' directory in a dictionary.

    Parameters
    ----------
    path : str
        Path to JSON file.

    Returns
    ----------
    dict
        The dictionary built.

    """

    with open(path) as json_file:
        # Init dict with default values
        dictionary = json.loads(json_file.read())
        # Update dict with types
        dictionary = allow_list_in_dict(dictionary)
        dictionary = force_types(dictionary)

    return dictionary


def force_types(dictionary: dict) -> dict:
    """
    This method allows to force the value types for the given
    dictionary.

    Parameters
    ----------
    dictionary : dict
        The dictionary with values expressed as strings.

    Returns
    -------
    dict
        The same dictionary with typed values.

    """
    for key in dictionary.keys():
        element = dictionary[key]
        if isinstance(element, dict):
            if "value" in element.keys():  # value => type
                if element["type"] == "bool":
                    dictionary[key]["value"] = element["value"] == "True"
                elif element["type"] == "int":
                    dictionary[key]["value"] = int(element["value"])
                elif element["type"] == "float":
                    dictionary[key]["value"] = float(element["value"])
                elif element["type"] == "tuple":
                    dictionary[key]["value"] = eval(element["value"])
            else:
                dictionary[key] = force_types(element)
    return dictionary


def allow_list_in_dict(dictionary: dict) -> dict:
    """
    This method translates string representations of lists
    in a dictionary to actual lists. Necessary for JSON
    representation of list values.

    Parameters
    ----------
    dictionary : dict
        The dictionary containing strings representing lists.

    Returns
    -------
    dict
        The same dictionary with actual lists.

    """

    for key in dictionary.keys():
        element = dictionary[key]
        if isinstance(element, dict):
            dictionary[key] = allow_list_in_dict(element)
        elif isinstance(element, str):
            if "[" in element:
                dictionary[key] = element.replace("[", "").replace("]", "").split(",")

    return dictionary


def read_vars(property_string: str) -> list:
    """
    This method reads all the variables contained in a constraints string

    Parameters
    ----------
    property_string : str
        A list of constraints contained in a single smt string

    Returns
    -------
    list
        The variables appearing in the constraints

    """
    variables = []

    for line in property_string.split('\n'):
        line = line.replace('(assert (<= ', '').replace('(assert (>= ', '').split(' ')

        if line[0] != '' and line[0] not in variables:
            variables.append(line[0])

    return variables


def write_smt_property(path: str, props: dict, dtype: str) -> None:
    # Create and write file
    with open(path, "w") as f:
        # Variables
        for p in props.values():
            if p.property_type == 'Local robustness':
                p.variables = read_vars(p.smt_string)
            for v in p.variables:
                f.write(f"(declare-fun {v} () {dtype})\n")
        f.write("\n")

        # Constraints
        for p in props.values():
            f.write(p.smt_string + "\n")
