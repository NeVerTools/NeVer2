import ctypes
import platform
import sys

from PyQt6.QtWidgets import QApplication

from never2.main_window import MainWindow
from never2.scripts import cli

if __name__ == "__main__":

    # GUI mode
    if len(sys.argv) == 1:
        APP_ID = u'org.neuralverification.never2.2.0'

        # Set taskbar icon on Windows
        if platform.system() == 'Windows':
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(APP_ID)
            sys.argv += ['-platform', 'windows:darkmode=2']  # TODO remove with styling

        app = QApplication(sys.argv)
        window = MainWindow()
        window.show()
        sys.exit(app.exec())

    # CLI mode
    elif len(sys.argv) == 2 and sys.argv[1] == '-h':
        cli.show_help()
    elif len(sys.argv) == 4 and sys.argv[1] == '-verify':
        cli.verify_model(sys.argv[2], sys.argv[3])
    else:
        cli.show_help()
