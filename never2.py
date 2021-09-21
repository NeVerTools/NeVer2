import ctypes
import os

if __name__ == "__main__":
    import sys
    from never2 import mainwindow
    from PyQt5 import QtWidgets

    myappid = u'org.neuralverification.coconet.0.1'
    if os.name == 'nt':
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

    app = QtWidgets.QApplication(sys.argv)
    window = mainwindow.MainWindow()

    window.show()
    sys.exit(app.exec_())
