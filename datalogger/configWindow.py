from utils import getResourcePath
from PyQt5.QtCore import Qt, QAbstractProxyModel, QModelIndex
from PyQt5.QtWidgets import QListWidgetItem
from PyQt5.uic import loadUiType

ConfigWindowUi, ConfigWindowBase = loadUiType(getResourcePath('ui/dataloggerConfigWindow.ui'))

class ConfigWindow(
        ConfigWindowBase, ConfigWindowUi):
    def __init__(self, dataloggerConfig, parent=None):
        ConfigWindowBase.__init__(self, parent)        
        self.setupUi(self)

        self.config = dataloggerConfig.clone()

        self.serialPort.textEdited.connect(self.serialPortTextEdited)
        self.deviceType.currentIndexChanged[str].connect(self.deviceTypeCurrentIndexChanged)

        self.serialPort.setText(self.config.serialPort)
        self.deviceType.setCurrentText(str(self.config.model))

    def keyPressEvent(self, event):
        event.ignore()

    def serialPortTextEdited(self, text):
        self.config.serialPort = text

    def deviceTypeCurrentIndexChanged(self, text):
        self.config.model = text