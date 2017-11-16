from PyQt5 import QtWidgets, QtCore
from PyQt5.QtGui import QIcon
from utils import getResourcePath
import sys
import uis
from backend import Backend
from configLoader import ConfigLoader
import vna


def main():
    qApp = QtWidgets.QApplication(sys.argv)
    backend = Backend()
    configLoader = ConfigLoader()
    window = uis.MainWindow(backend, configLoader)

    backend.register_instrument("vna", vna.Driver)
    configLoader.registerInstrument("vna", vna.Config)
    window.registerInsturmentType("vna", vna.DataWindow, vna.ConfigWindow)
    window.registerInstrumentIcon(vna.Config, QIcon(getResourcePath('images/networkAnalyser.png')))
    window.show()

    if(len(sys.argv) > 1):
        window.openConfig(sys.argv[1])

    sys.exit(qApp.exec_())


if __name__ == '__main__':
    main()
