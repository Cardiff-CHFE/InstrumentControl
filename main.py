from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import QListWidgetItem
from PyQt5.QtGui import QIcon
import sys
import uis
from backend import Backend
import vna


def main():
    qApp = QtWidgets.QApplication(sys.argv)
    backend = Backend()
    backend.register_instrument("vna", vna.Config, vna.Driver)
    window = uis.MainWindow(backend)
    window.registerInsturmentType("vna", vna.DataWindow)
    window.show()
    # ilist = InstrumentList()
    # window.instrumentList.setModel(ilist)
    sys.exit(qApp.exec_())


if __name__ == '__main__':
    main()
