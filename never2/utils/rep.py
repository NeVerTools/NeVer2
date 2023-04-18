"""
Module rep.py

This module contains utility methods for the representation of objects

Author: Andrea Gimelli, Giacomo Rosato, Stefano Demarchi

"""

import json
import traceback

from never2 import RES_DIR
from never2.view.ui.dialog import MessageDialog, MessageType

JSON_PATH = RES_DIR + '/json'


def read_json_data() -> tuple:
    with open(JSON_PATH + '/blocks.json', 'r') as fdata:
        block_data = json.load(fdata)

    with open(JSON_PATH + '/properties.json', 'r') as fdata:
        prop_data = json.load(fdata)

    with open(JSON_PATH + '/functionals.json', 'r') as fdata:
        func_data = json.load(fdata)

    return block_data, prop_data, func_data


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


def text2tuple(text: str) -> tuple:
    """
    This method takes a string in format '(n,m,l)...' and
    converts it into a variable of type tuple with the given dimensions.

    Parameters
    ----------
    text: str
        Input string to convert.

    Returns
    ----------
    tuple
        The converted tensor set.

    """

    output_tuple = tuple()
    text = str(text)

    if len(text.split(",")) > 1:
        for token in text.replace("(", "").replace(")", "").split(","):
            if token != "":
                num = int(token)
                output_tuple += (num,)
    else:
        output_tuple += (int(text),)

    return output_tuple


def tuple2text(tup: tuple, prod: bool = True) -> str:
    """
    This function takes in input a tuple and return a string in a new format

    Parameters
    ----------
    tup : tuple
        A tuple of elements

    prod : boolean
        Determines if the digits of the tuple must be separated by 'x' or ','

    Returns
    -------
    new_format : str
        Either the tuple formatted as 'a x b x c ...' if prod is True, 'a, b, c ...' otherwise

    """

    dim_list = list(str(tup).replace('(', '').strip().replace(')', '').strip().split(','))
    if '' in dim_list:
        dim_list.remove('')

    if len(dim_list) == 1:
        return str(tup).replace('(', '').replace(')', '').replace(',', '')

    if prod:
        separator = ' x '
    else:
        separator = ', '

    dim_list = [x.strip() for x in str(tup).replace('(', '').strip().replace(')', '').strip().split(',')]
    new_format = separator.join(dim_list)

    return new_format


def format_data(params: dict) -> dict:
    """
    This function re-formats a complete dictionary of block attributes in the format
    <key> : str
    <value> : expected type

    Parameters
    ----------
    params : dict
        The original dictionary

    Returns
    ----------
    dict
        The formatted dictionary

    """

    converted_dict = dict()
    value = None

    try:
        for param_name, param_value in params.items():
            if param_value[1] == '':
                continue
            if param_value[2] == 'Tensor':
                value = text2tuple(param_value[1])
            elif param_value[2] == 'int':
                value = int(param_value[1])
            elif param_value[2] == 'list of ints':
                value = list(map(int, param_value[1].split(', ')))
            elif param_value[2] == 'boolean':
                value = param_value[1] == 'True'
            elif param_value[2] == 'float':
                value = float(param_value[1])
            converted_dict[param_name] = value
    except Exception as e:
        dialog = MessageDialog(str(e), MessageType.ERROR)
        dialog.exec()

    return converted_dict


def dump_exception(e: Exception):
    # TODO format
    traceback.print_exc()
