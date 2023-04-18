import ctypes
import platform
import sys

from PyQt6.QtWidgets import QApplication
from never2.main_window import NeVerWindow

if __name__ == "__main__":

    APP_ID = u'org.neuralverification.never2.2.0'

    # Set taskbar icon on Windows
    if platform.system() == 'Windows':
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(APP_ID)
        sys.argv += ['-platform', 'windows:darkmode=2']  # TODO remove with styling

    app = QApplication(sys.argv)
    window = NeVerWindow()
    window.show()
    sys.exit(app.exec())
