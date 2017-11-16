from utils import getResourcePath
from PyQt5.uic import loadUiType
from PyQt5.QtCore import QAbstractProxyModel, Qt
from PyQt5.QtWidgets import QDialog
from keyValueModel import KeyValueModel
from schemaDelegate import SchemaDelegate

EditInstrumentsDialogUI, EditInstrumentsDialogBase = loadUiType(getResourcePath('ui/editInstrumentsDialog.ui'))


class EditInstrumentsDialog(EditInstrumentsDialogBase, EditInstrumentsDialogUI):
    def __init__(self, instrumentConfig, icons, configWindows, parent=None):
        EditInstrumentsDialogBase.__init__(self, parent)
        self.setupUi(self)

        self.config = instrumentConfig.clone()
        self.configModel = KeyValueModel(self.config)
        self.configModel.icons = icons
        self.configWindows = configWindows
        self.instrumentList.setModel(self.configModel)
        self.instrumentListDelegate = SchemaDelegate()
        self.instrumentList.setItemDelegate(self.instrumentListDelegate)
        self.instrumentList.setModelColumn(0)
        self.instrumentList.doubleClicked.connect(self.doubleClicked)

    def doubleClicked(self, index):
        config = KeyValueModel.valueOf(index)
        try:
            wnd = self.configWindows[config.type_](config)
            if wnd.exec_() == QDialog.Accepted:
                config.parent.setChild(config.row, wnd.config)
        except Exception:
            raise
