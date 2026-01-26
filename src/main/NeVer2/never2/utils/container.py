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

    Methods
    ----------
    check_variables_size(Optional[int, tuple])
        Procedure to check compatibility between dimensions

    """

    def __init__(self, smt_str: str = '', variables: list = None, name: str = 'Generic SMT'):
        if variables is None:
            variables = []

        self.smt_string = smt_str
        self.variables = variables
        self.name = name

    def check_variables_size(self, shape) -> bool:
        """
        This method checks whether the number of variables in the property
        is consistent with a given size as an int or a tuple

        Parameters
        ----------
        shape : Optional[int, tuple]
            The shape to check, either as a single number or a tuple

        Returns
        ----------
        bool
            True if the dimensions are consistent, False otherwise

        """

        if isinstance(shape, int):
            return len(self.variables) == shape
        elif isinstance(shape, tuple):
            n = 1
            for e in shape:
                n *= e
            return len(self.variables) == n
        else:
            return False
