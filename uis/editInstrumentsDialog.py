from utils import getResourcePath
from PyQt5.uic import loadUiType
from PyQt5.QtCore import QAbstractProxyModel, Qt
from PyQt5.QtWidgets import QDialog, QListWidgetItem

EditInstrumentsDialogUI, EditInstrumentsDialogBase = loadUiType(getResourcePath('ui/editInstrumentsDialog.ui'))


class EditInstrumentsDialog(EditInstrumentsDialogBase, EditInstrumentsDialogUI):
    def __init__(self, instrumentConfig, icons, configWindows, parent=None):
        EditInstrumentsDialogBase.__init__(self, parent)
        self.setupUi(self)

        self.config = instrumentConfig.clone()
        self.configWindows = configWindows
        self.icons = icons
        for key, value in self.config.instruments.items():
            item = QListWidgetItem(key)
            item.setIcon(self.icons[type(value)])
            self.instrumentList.addItem(item)
    
        self.instrumentList.itemDoubleClicked.connect(self.instrumentListDoubleClicked)
        self.datadir.editingFinished.connect(self.datadirEditingFinished)

        self.datadir.setText(self.config.datadir)

    def instrumentListDoubleClicked(self, item):
        instrumentName = item.text()
        instrumentConfig = self.config.instruments[instrumentName]
        wnd = self.configWindows[instrumentConfig.type_](instrumentConfig)
        if wnd.exec_() == QDialog.Accepted:
            self.config.instruments[instrumentName] = wnd.config

    def datadirEditingFinished(self):
        self.config.datadir = self.datadir.text()
