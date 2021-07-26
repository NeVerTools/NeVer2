from PyQt5.QtWidgets import QLabel, QComboBox, QLineEdit, QPlainTextEdit, QPushButton

import never2.view.styles as style


class CustomLabel(QLabel):
    def __init__(self, text: str = '', color: str = style.WHITE):
        super(CustomLabel, self).__init__(text)
        self.setStyleSheet("color: " + color + ";" +
                           "border: none;" +
                           "padding: 2px 0px 2px 2px;")


class CustomComboBox(QComboBox):
    def __init__(self, color: str = style.WHITE):
        super(CustomComboBox, self).__init__()
        self.setStyleSheet("color: " + color + ";" +
                           "background-color: " + style.GREY_2 + ";" +
                           "border: none;" +
                           "padding: 2px;")


class CustomTextBox(QLineEdit):
    def __init__(self, text: str = '', color: str = style.WHITE):
        super(CustomTextBox, self).__init__(text)
        self.setStyleSheet("color: " + color + ";" +
                           "background-color: " + style.GREY_2 + ";" +
                           "border: none;" +
                           "padding: 2px;")


class CustomTextArea(QPlainTextEdit):
    def __init__(self, color: str = style.WHITE):
        super(CustomTextArea, self).__init__()
        self.setStyleSheet("color: " + color + ";" +
                           "background-color: " + style.GREY_2 + ";" +
                           "border: none;" +
                           "padding: 2px;" +
                           "QPlainTextEdit::placeholder {" +
                           "color: " + style.GREY_4 + ";" +
                           "}")


class CustomButton(QPushButton):
    def __init__(self, text: str = ''):
        super(CustomButton, self).__init__(text)
        self.setStyleSheet(style.BUTTON_STYLE)
