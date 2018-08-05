from utils import getResourcePath
from PyQt5.QtCore import Qt, QAbstractProxyModel, QModelIndex
from PyQt5.QtWidgets import QListWidgetItem
from PyQt5.uic import loadUiType

ConfigWindowUi, ConfigWindowBase = loadUiType(getResourcePath('ui/visaScriptConfigWindow.ui'))

class ConfigWindow(
        ConfigWindowBase, ConfigWindowUi):
    def __init__(self, visaScriptConfig, parent=None):
        ConfigWindowBase.__init__(self, parent)        
        self.setupUi(self)

        self.config = visaScriptConfig.clone()

        self.resourceId.textEdited.connect(self.resourceIdTextEdited)
        self.script.textChanged.connect(self.scriptTextChanged)

        self.resourceId.setText(self.config.resource)
        self.script.setPlainText(self.config.script)

    def keyPressEvent(self, event):
        event.ignore()

    def resourceIdTextEdited(self, text):
        self.config.resource = text

    def scriptTextChanged(self):
        self.config.script = self.script.toPlainText()

    

