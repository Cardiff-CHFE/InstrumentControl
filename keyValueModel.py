from PyQt5.QtCore import QAbstractItemModel, QModelIndex, Qt
from traceback import print_exc

class KeyValueModel(QAbstractItemModel):
    def __init__(self, root):
        super().__init__()
        root.dataModel = self
        self._root = root
        self.icons = {}

    @property
    def root(self):
        return self._root

    def columnCount(self, index):
        return 2

    def rowCount(self, index):
        if index.isValid():
            try:
                return self.valueOf(index).childCount()
            except AttributeError:
                return 0
        return self._root.childCount()

    def index(self, row, column, parentIn=None):
        if not parentIn or not parentIn.isValid():
            parent = self._root
        else:
            parent = self.valueOf(parentIn)

        try:
            parent.child(row) # Check child exists
            return QAbstractItemModel.createIndex(self, row, column, parent)
        except IndexError:
            return QModelIndex()

    def parent(self, index):
        if index.isValid():
            node = index.internalPointer()
            try:
                p = node.parent
                if p is not None:
                    return QAbstractItemModel.createIndex(self, node.row, 0, p)
            except AttributeError:
                pass
        return QModelIndex()

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None
        column = index.column()
        if column == 0:
            if role == Qt.DisplayRole or role == Qt.EditRole:
                try:
                    return self.keyOf(index)
                except Exception:
                    pass
            elif role == Qt.DecorationRole:
                type_ = type(self.valueOf(index))
                try:
                    return self.icons[type_]
                except KeyError:
                    pass
        elif column == 1:
            if role == Qt.DisplayRole:
                return str(self.valueOf(index))
            elif role == Qt.EditRole:
                return self.valueOf(index)
        return None

    def flags(self, index):
        if not index.isValid():
            return QAbstractItemModel.flags(self, index)
        column = index.column()
        editable = False
        parent = index.internalPointer()

        if column == 0:
            try:
                editable = parent.canEditKeys()
            except AttributeError:
                editable = False
        elif column == 1:
            editable = True

        result = Qt.ItemIsSelectable | Qt.ItemIsEnabled
        if editable:
            result = result | Qt.ItemIsEditable
        return result

    def setData(self, index, value, role):
        if not index.isValid() or role != Qt.EditRole:
            return False
        parent = index.internalPointer()

        try:
            if index.column() == 0:
                parent.setChildKey(index.row(), value)
                return True
            elif index.column() == 1:
                parent.setChild(index.row(), value)
                return True
        except Exception as ex:
            print_exc()
            pass
        return False

    def insertRows(self, row, count, parent=QModelIndex()):
        if parent.isValid():
            node = self.valueOf(parent)
        else:
            node = self._root
        try:
            node.insertChildren(row, count)
            return True
        except Exception:
            return False

    def removeRows(self, row, count, parent=QModelIndex()):
        if parent.isValid():
            node = self.valueOf(parent)
        else:
            node = self._root

        try:
            node.removeChildren(row, count)
            return True
        except Exception:
            return False

    def moveRows(self, sourceParent, sourceRow, count, destParent, destChild):
        if sourceParent != destParent:
            return False
        if sourceParent.isValid():
            node = self.valueOf(sourceParent)
        else:
            node = self._root

        try:
            node.moveChildren(sourceRow, count, destChild)
            return True
        except Exception:
            return False

    # custom methods
    def indexOf(self, node, column):
        return self.createIndex(node.row, column, node.parent)

    def valueOf(self, index):
        return index.internalPointer().child(index.row())

    def keyOf(self, index):
        return index.internalPointer().childKey(index.row())

    def updateChild(self, parent, row):
        childIndex = self.createIndex(row, 1, parent)
        self.dataChanged.emit(childIndex, childIndex)

    def updateChildKeys(self, parent, row, count):
        childIndex0 = self.createIndex(row, 0, parent)
        childIndex1 = self.createIndex(row+count-1, 0, parent)
        self.dataChanged.emit(childIndex0, childIndex1)

    def beginInsertChildren(self, parent, row, count):
        parentIndex = self.indexOf(parent, 1)
        self.beginInsertRows(parentIndex, row, row+count-1)

    def endInsertChildren(self, parent):
        self.endInsertRows()

    def beginRemoveChildren(self, parent, row, count):
        parentIndex = self.indexOf(parent, 1)
        self.beginRemoveRows(parentIndex, row, row+count-1)

    def endRemoveChildren(self, parent):
        self.endRemoveRows()

    def beginMoveChildren(self, parent, row, count, dest):
        parentIndex = self.indexOf(parent, 1)
        self.beginMoveRows(parentIndex, row, row+count-1, parentIndex, dest)

    def endMoveChildren(self, parent):
        self.endMoveRows()
