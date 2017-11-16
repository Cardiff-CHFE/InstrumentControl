from PyQt5.QtWidgets import QStyledItemDelegate, QSpinBox, QLineEdit, QCheckBox
from PyQt5.QtCore import Qt
from uis.siSpinBox import SISpinBox
from schema import TInt, TFloat, TBool, TString
from traceback import print_exc


class SchemaDelegate(QStyledItemDelegate):
    def __init__(self):
        QStyledItemDelegate.__init__(self)

        def match(dtype):
            def matcher(value):
                return isinstance(value, dtype)
            return matcher

        self.delegates = [
            (match(TInt), SpinBoxDelegate),
            (match(TString), LineEditDelegate),
            (match(TBool), CheckBoxDelegate),
            (match(TFloat), SISpinDelegate)
        ]

    def findDelegate(self, value):
        dtype = value.parent.dtypeForRow(value.row)
        for matcher, delegate in self.delegates:
            if matcher(dtype):
                return delegate(dtype)
        return None

    def createEditor(self, parent, option, index):
        column = index.column()
        if column == 0:
            return QLineEdit(parent)
        elif column == 1:
            value = index.data(Qt.EditRole)
            delegate = self.findDelegate(value)
            if delegate:
                return delegate.createEditor(parent, option, value)

        QStyledItemDelegate.createEditor(self, parent, option, index)

    def setEditorData(self, editor, index):
        column = index.column()
        if column == 0:
            editor.setText(index.data(Qt.EditRole))
            return
        elif column == 1:
            value = index.data(Qt.EditRole)
            delegate = self.findDelegate(value)
            if delegate:
                delegate.setEditorData(editor, value)
                return
        QStyledItemDelegate.setEditorData(self, editor, index)

    def setModelData(self, editor, model, index):
        try:
            column = index.column()
            if column == 0:
                model.setData(index, editor.text(), Qt.EditRole)
            elif column == 1:
                value = index.data(Qt.EditRole)
                delegate = self.findDelegate(value)
                if delegate:
                    value = delegate.getEditorData(editor)
                    model.setData(index, value, Qt.EditRole)
        except Exception as ex:
            print_exc()
            raise

    def updateEditorGeometry(self, editor, option, index):
        editor.setGeometry(option.rect)


class SpinBoxDelegate():
    def __init__(self, dtype):
        self.dtype = dtype

    def createEditor(self, parent, option, value):
        editor = QSpinBox(parent)
        editor.setMinimum(0)
        editor.setMaximum(9999)
        return editor

    def setEditorData(self, editor, value):
        editor.setValue(value)

    def getEditorData(self, editor):
        return editor.value()


class LineEditDelegate():
    def __init__(self, dtype):
        self.dtype = dtype

    def createEditor(self, parent, option, value):
        return QLineEdit(parent)

    def setEditorData(self, editor, value):
        editor.setText(value)

    def getEditorData(self, editor):
        return editor.text()


class CheckBoxDelegate():
    def __init__(self, dtype):
        self.dtype = dtype

    def createEditor(self, parent, option, value):
        return QCheckBox(parent)

    def setEditorData(self, editor, value):
        editor.setChecked(bool(value))

    def getEditorData(self, editor):
        return editor.isChecked()


class SISpinDelegate():
    def __init__(self, dtype):
        self.suffix = dtype.suffix
        self.minimum = dtype.minimum
        self.maximum = dtype.maximum

    def createEditor(self, parent, option, index):
        scientificSpin = SISpinBox(parent)
        scientificSpin.setMinimum(self.minimum)
        scientificSpin.setMaximum(self.maximum)
        #FIXME
        # scientificSpin.setSuffix(self.suffix)
        return scientificSpin

    def setEditorData(self, editor, value):
        editor.setValue(value)

    def getEditorData(self, editor):
        return editor.value()
