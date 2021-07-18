if __name__ == "__main__":
    import sys
    from never2 import mainwindow
    from PyQt5 import QtWidgets

    app = QtWidgets.QApplication(sys.argv)
    window = mainwindow.MainWindow()

    window.show()
    sys.exit(app.exec_())
