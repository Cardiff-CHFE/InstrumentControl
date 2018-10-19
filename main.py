from PyQt5 import QtWidgets, QtCore
from PyQt5.QtGui import QIcon
from utils import getResourcePath
import sys
import uis
from backend import Backend
from configLoader import ConfigLoader
import vna
import visaScript
import datalogger


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
    backend.register_instrument(visaScript.Config, visaScript.Driver)
    configLoader.registerInstrument(visaScript.Config)
    window.registerInsturmentType(
        "visaScript",
        visaScript.DataWindow,
        visaScript.ConfigWindow,
        QIcon(getResourcePath('images/dcSupply.png')),
        visaScript.Config({
            'script': 'record_wait()\nlog("Record start")'
        }))

    backend.register_instrument(datalogger.Config, datalogger.Driver)
    configLoader.registerInstrument(datalogger.Config)
    window.registerInsturmentType(
        "Data Logger",
        datalogger.DataWindow,
        datalogger.ConfigWindow,
        QIcon(getResourcePath('images/dcSupply.png')),
        datalogger.Config({
            'model': '1365'
        }))
    window.show()

    if(len(sys.argv) > 1):
        window.openConfig(sys.argv[1])

    sys.exit(qApp.exec_())


if __name__ == '__main__':
    main()
