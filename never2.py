"""
NeVer2 is a tool for the verification of neural networks.

The project is hosted at NeverTools (https://github.com/nevertools/) and comprises
the Python API pyNeVer and the complete GUI tool NeVer2 - this file. The API
enables NeVer2 to provide a graphical interface towards the capabilities of designing,
learning and verifying neural networks, all in a single environment.

Authors
-------
Stefano Demarchi
Dario Guidotti
Armando Tacchella
Luca Pulina

Contributors
------------
Andrea Gimelli
Giacomo Rosato
Karim Pedemonte
Pedro Henrique Simão Achete
Elena Botoeva

"""

import sys

from PyQt6.QtWidgets import QApplication

from never2.main_window import MainWindow

if __name__ == '__main__':
    # GUI mode
    APP_ID = u'org.neuralverification.never2.2.0'

    app = QApplication(sys.argv)
    app.setStyle('fusion')
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
