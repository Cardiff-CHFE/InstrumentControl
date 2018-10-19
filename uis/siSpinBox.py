import re
from PyQt5.QtGui import QValidator
from PyQt5.QtCore import Qt, QVariant
from PyQt5.QtWidgets import QDoubleSpinBox, QStyledItemDelegate
from math import inf
from utils import float_to_si, si_to_float, si_prefixes

allowed_chars = 'YZEPTGMkmunpfazy0123456789.-'

class SISpinBox(QDoubleSpinBox):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setDecimals(1000)

    def validate(self, text, position):
        try:
            si_to_float(text)
            return QValidator.Acceptable, text, position
        except (ValueError, KeyError):
            if text == "-":
                return QValidator.Intermediate, text, position
            return QValidator.Invalid, text, position

    def fixup(self, text):
        text = ''.join(c for c in text if c in allowed_chars)
        return text

    def valueFromText(self, text):
        return si_to_float(text)

    def textFromValue(self, value):
        return float_to_si(value)

    def stepBy(self, steps):
        try:
            exp = si_prefixes[self.cleanText()[-1]]
            self.setValue(self.value()+(steps*exp)/10)
        except KeyError:
            pass
