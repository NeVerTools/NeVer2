"""
Module validator.py

This module contains the validations for QWidgets

Author: Andrea Gimelli, Giacomo Rosato, Stefano Demarchi

"""

from PyQt6.QtCore import QLocale, QRegularExpression
from PyQt6.QtGui import QIntValidator, QDoubleValidator, QRegularExpressionValidator


class ArithmeticValidator:
    """
    This class collects the possible validators for
    the editing dialogs.

    INT : (QIntValidator)
        Integer validator.
    FLOAT : (QDoubleValidator)
        Floating-point validator.
    TENSOR : (QRegExpValidator)
        Tensor ("nxmxl", "nXmXl", "n,m,l") with n, m, l
        integers validator.
    TENSOR_LIST : (QRegExpValidator)
        List of Tensors.

    """

    locale = QLocale(QLocale.Language.English, QLocale.Country.UnitedStates)

    INT = QIntValidator()
    INT.setLocale(locale)

    FLOAT = QDoubleValidator()
    FLOAT.setLocale(locale)

    TENSOR = QRegularExpressionValidator(QRegularExpression('(([0-9])+(,\s?[0-9]+)*)'))
    TENSOR.setLocale(locale)

    SAMPLE = QRegularExpressionValidator(QRegularExpression('^(?:\d+(?:\.\d*)?|\.\d+)(?:,(?:\d+(?:\.\d*)?|\.\d+))*$'))
