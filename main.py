from PyQt5 import QtWidgets, QtCore
from PyQt5.QtGui import QIcon
from utils import getResourcePath
import sys
import uis
from backend import Backend
from configLoader import ConfigLoader
import vna
import visaScript


def main():
    qApp = QtWidgets.QApplication(sys.argv)
    backend = Backend()
    configLoader = ConfigLoader()
    window = uis.MainWindow(backend, configLoader)

    backend.register_instrument(vna.Config, vna.Driver)
    configLoader.registerInstrument(vna.Config)
    window.registerInsturmentType(
        "Vna",
        vna.DataWindow,
        vna.ConfigWindow,
        QIcon(getResourcePath('images/networkAnalyser.png')),
        vna.Config({
            'model': 'simulated',
            'segments': {
                'TM010' : {
                    'type': 'Electric',
                    'f0': 2500700000.0,
                    'span': 1000000.0,
                    'points': 201,
                    'ifbw': 1000.0,
                    'power': 0.0
                }
            }
        }))
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
