"""
Module container.py

This module contains classes for the compact representation of objects

Author: Andrea Gimelli, Giacomo Rosato, Stefano Demarchi

"""


class PropertyContainer:
    """
    This class is a container for a property object

    Attributes
    ----------
    smt_string : str
        String in the SMT format describing the property

    variables : list
        Variables used in the property

    name : str
        String associated to the property type

    """

    def __init__(self, smt_str: str = '', variables: list = None, name: str = 'Generic SMT'):
        if variables is None:
            variables = []

        self.smt_string = smt_str
        self.variables = variables
        self.name = name
