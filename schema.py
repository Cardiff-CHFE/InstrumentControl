import collections
from utils import float_to_si
from math import inf

__all__ = [
    'MObject', 'MDict', 'MInt', 'MFloat', 'MString',
    'TObject', 'TDict', 'TInt', 'TFloat', 'TString',
]


class T:
    __slots__ = []

    def __call__(self, value):
        raise NotImplementedError()


class TDict(T):
    def __init__(self, dtype):
        self.dtype = dtype

    def __call__(self, value=None):
        return MDict(self.dtype, value)

    def __eq__(self, other):
        return type(other) == type(self) and other.dtype == self.dtype


class TList(T):
    def __init__(self, dtype):
        self.dtype = dtype

    def __call__(self, value=None):
        return MList(self.dtype, value)

    def __eq__(self, otheR):
        return type(other) == type(self) and other.dtype == self.dtype


class TUnion(T):
    def __init__(self, dtypes, key="type"):
        self.dtypes = dtypes
        self.key = key

    def __call__(self, value=None):
        # Special handling to copy TObjects on assignment
        if isinstance(value, TObject):
            for inst in self.dtypes.values():
                if isinstance(value, inst):
                    return inst(value)
            raise ValueError(
                "Object of type {} not in union".format(type(value).__name__))

        dtype = value[self.key]
        return self.dtypes[dtype](value)

    def __eq__(self, other):
        return type(other) == type(self) and other.objs == self.objs


class TInt(T):
    def __init__(self, default=0):
        self.default = default

    # TODO Implement bounds checking
    def __call__(self, value=None):
        if value is None:
            value = self.default
        return MInt(value)

    def __eq__(self, other):
        return type(other) == type(self)


class TFloat(T):
    def __init__(self, default=0.0, minimum=-999.999999e24,
                 maximum=999.999999e24, suffix=""):
        self.default = default
        self.suffix = suffix
        self.minimum = minimum
        self.maximum = maximum

    # TODO Implement bounds checking
    def __call__(self, value=None):
        if value is None:
            value = self.default
        if not self.minimum < value < self.maximum:
            raise ValueError("Value out of range")
        return MFloat(value, suffix=self.suffix)

    def __eq__(self, other):
        return type(other) == type(self)


class TBool(T):
    def __init__(self, default=False):
        self.default = default

    # TODO Implement bounds checking
    def __call__(self, value=None):
        if value is None:
            value = self.default
        return MBool(value)

    def __eq__(self, other):
        return type(other) == type(self)


class TString(T):
    def __init__(self, default=""):
        self.default = default
    # TODO Implement bounds checking
    def __call__(self, value=None):
        if value is None:
            value = self.default
        return MString(value)

    def __eq__(self, other):
        return type(other) == type(self)


class BaseCollection(object):
    def __init__(self, items=None):
        self._dataModel = None
        self._data = []
        if items is not None:
            for row, (key, value) in enumerate(items):
                self._data.append((key, self._newChild(row, value)))

    def dtypeForRow(self, row):
        """Override this to get the data type of a row"""
        raise NotImplementedError()

    def keyForRow(self, row):
        """Override this to generate a key for a row"""
        raise NotImplementedError()

    def canEditKeys(self):
        """Override this to indicate if keys can be edited"""
        raise NotImplementedError()

    def canMoveChildren(self):
        """Override this to indicate if children can be moved"""
        raise NotImplementedError()

    def updateRowKey(self, row):
        """Override this to update keys of rows that have moved"""
        return None

    def reprRow(self, row):
        """
        Override this to return a repr string for the row.

        Some examples include "[2]", "['key']", or ".someProperty"
        """
        raise NotImplementedError()

    def clone(self):
        """Override this to clone self"""
        raise NotImplementedError()

    def rowForKey(self, key):
        for i, (row, _) in enumerate(self._data):
            if row == key:
                return i
        raise KeyError()

    def childCount(self):
        return len(self._data)

    def child(self, row):
        return self._data[row][1]

    def childKey(self, row):
        return self._data[row][0]

    def children(self):
        for row in self._data:
            yield row

    def setChild(self, row, value):
        self._data[row] = (self.childKey(row), self._newChild(row, value))
        if self.dataModel is not None:
            self.dataModel.updateChild(self, row)

    def setChildKey(self, row, value):
        self._data[row] = (str(value), self.child(row))
        if self.dataModel is not None:
            self.dataModel.updateChildKeys(self, row, 1)

    def addChild(self, value, key=None):
        self.insertChild(len(self._data), value, key)

    def insertChild(self, row, value, key=None):
        if self.dataModel is not None:
            self.dataModel.beginInsertChildren(self, row, 1)

        if key is None:
            key = self.keyForRow(row)
        else:
            key = str(key)
        self._data.insert(row, (key, self._newChild(row, value)))

        if self.dataModel is not None:
            self.dataModel.endInsertChildren(self)

        self._updateKeys(row, len(self._data))

    def insertChildren(self, row, count):
        if self.dataModel is not None:
            self.dataModel.beginInsertChildren(self, row, count)

        for i in range(row, row+count):
            key = self.keyForRow(i)
            self._data.insert(i, (key, self._newChild(i)))

        if self.dataModel is not None:
            self.dataModel.endInsertChildren(self)

        self._updateKeys(row+count, len(self._data))

    def removeChild(self, row):
        self.removeChildren(row, 1)

    def removeChildren(self, row, count):
        if self.dataModel is not None:
            self.dataModel.beginRemoveChildren(self, row, count)

        for i in range(count):
            del self._data[row]

        if self.dataModel is not None:
            self.dataModel.endRemoveChildren(self)

        self._updateKeys(row, len(self._data))

    def moveChildren(self, row, count, dest):
        if row <= dest < row+count:
            raise RuntimeError("Destination must not be within source")
        elif dest == row+count:
            return

        if self.dataModel is not None:
            self.dataModel.beginMoveChildren(self, row, count, dest)

        if dest > row:
            dest -= count
        temp = self._data[row:row+count]
        del self._data[row:row+count]
        self._data[dest:dest] = temp

        if self.dataModel is not None:
            self.dataModel.endMoveChildren(self)

        self._updateKeys(min(row, dest), max(row+count, dest+count))

    def _newChild(self, row, value=None):
        value = self.dtypeForRow(row)(value)
        value.parent = self
        value.row = row
        value.dataModel = self.dataModel
        return value

    def _updateKeys(self, start, end):
        keysChanged = False
        for row in range(start, end):
            self.child(row).row = row
            newKey = self.updateRowKey(row)
            if newKey is not None:
                self._data[row] = (newKey, self.child(row))
                keysChanged = True
        if keysChanged:
            if self.dataModel is not None:
                self.dataModel.updateChildKeys(self, start, end-start)

    @property
    def dataModel(self):
        return self._dataModel

    @dataModel.setter
    def dataModel(self, dataModel):
        self._dataModel = dataModel
        for _, value in self._data:
            value.dataModel = dataModel

    def __repr__(self):
        path = ""
        parent = self.parent
        while parent is not None:
            path = parent.reprRow(self.row) + path
        return path


class PropertyInternal:
    __slots__ = ['dtype', 'name', 'row']

    def __init__(self, row):
        self.row = row

    def __get__(self, instance, owner=None):
        if instance is None:
            return self
        return instance.child(self.row)

    def __set__(self, instance, value):
        instance.setChild(self.row, value)


class TObjectMeta(type):
    def __new__(cls, name, bases, dct):
        row = 0
        dtypes = collections.OrderedDict()
        for key, value in dct.items():
            if isinstance(value, T):
                dtypes[key] = value
                dct[key] = PropertyInternal(row)
                row += 1
        dct['dtypes'] = dtypes
        return super().__new__(cls, name, bases, dct)


class TObject(BaseCollection, metaclass=TObjectMeta):
    def __init__(self, data=None):
        self._dataModel = None
        self.parent = None
        self.row = 0
        # Extras are items that we don't care about, but should still save
        # when serializing.
        self._extras = {}
        if data is not None:
            if isinstance(data, type(self)):
                super().__init__(data.children())
                self._extras = data._extras
            else:
                keys = set(data.keys())
                items = []
                for prop in self.dtypes:
                    key = prop.rstrip('_')
                    try:
                        items.append((key, data[key]))
                        keys.remove(key)
                    except KeyError:
                        items.append((key, None))
                super().__init__(items)
                # Store unused keys in the extras dict
                for key in keys:
                    self._extras[key] = data[key]

    def serialize(self):
        data = self._extras.copy()
        for key, value in self.children():
            data[key] = value.serialize()
        return data

    def __str__(self):
        return ""

    def dtypeForRow(self, row):
        return list(self.dtypes.values())[row]

    def canEditKeys(self):
        return False

    def reprRow(self, row):
        return ".{}".format(list(self.dtypes.keys())[row])

    def setChildKey(self, row, value):
        raise RuntimeError("Cannot change TObject keys")

    def insertChild(self, row, value, key=None):
        raise RuntimeError("Cannot insert into TObject")

    def insertChildren(self, row, count):
        raise RuntimeError("Cannot insert into TObject")

    def moveChildren(self, row, count, dest):
        raise RuntimeError("Cannot move children of TObject")

    def removeChildren(self, row, count):
        raise RuntimeError("Cannot remove from TObject")

    def clone(self):
        return type(self)(self)


class MDict(BaseCollection, collections.MutableMapping):
    def __init__(self, dtype, items=None):
        self.dtype = dtype
        if items is not None:
            items = items.items()
        super().__init__(items)

    def dtypeForRow(self, row):
        return self.dtype

    def keyForRow(self, row):
        fmt = "New item {}"
        i = 1
        while True:
            key = fmt.format(i)
            try:
                self.rowForKey(key)
                i += 1
            except KeyError:
                return key

    def canEditKeys(self):
        return True

    def __setitem__(self, key, value):
        try:
            row = self.rowForKey(key)
            self.setChild(row, value)
        except KeyError:
            super().addChild(value, key)

    def __getitem__(self, key):
        row = self.rowForKey(key)
        return self.child(row)

    def __delitem__(self, key):
        row = self.rowForKey(key)
        self.removeChildren(row, 1)

    def __iter__(self):
        for row in self.children():
            yield row[0]

    def items(self):
        """Optional, but improves efficiency of iteration"""
        return self.children()

    def values(self):
        """Optional, but improves efficiency of iteration"""
        for row in self.children():
            yield row[1]

    def __len__(self):
        return self.childCount()

    def __str__(self):
        return ""

    def serialize(self):
        data = {}
        for key, value in self.children():
            value = value.serialize()
            data[key] = value
        return data

    def setChildKey(self, row, value):
        try:
            if row != self.rowForKey(value):
                raise ValueError("Key already exists")
        except KeyError:
            pass
        super().setChildKey(row, value)

    def insertChild(self, row, value, key=None):
        if key is not None:
            try:
                self.rowForKey(key)
                raise ValueError("Key already exists")
            except KeyError:
                super().insertChild(row, value, key)
        else:
            super().insertChild(row, value)

    def clone(self):
        return type(self)(self.dtype, self)


class MList(BaseCollection, collections.MutableSequence):
    def __init__(self, dtype, items=None):
        self.dtype = dtype
        if items is not None:
            items = enumerate(items, start=1)
        super().__init__(items)

    def __getitem__(self, index):
        return self.child(index)

    def __setitem__(self, index, value):
        self.setChild(index, value)

    def __delitem__(self, index):
        self.removeChildren(index, 1)

    def __len__(self):
        return self.childCount()

    def insert(self, index, value):
        self.insertChild(index, value)

    def serialize(self):
        data = []
        for _, value in self.children():
            data.append(value.serialize())
        return data

    def __str__(self):
        return ""

    def dtypeForRow(self, row):
        return self.dtype

    def keyForRow(self, row):
        return str(row + 1)

    def canEditKeys(self):
        return False

    def updateRowKey(self, row):
        return str(row+1)

    def setChildKey(self, row, value):
        """List keys cannot be changed"""
        pass

    def insertChild(self, row, value, key=None):
        """Ignore the key and let the list choose it's own"""
        super().insertChild(row, value)

    def clone(self):
        return type(self)(self.dtype, self)


class MInt(int):
    def __init__(self, *args, **kwargs):
        self.dataModel = None
        self.parent = None
        self.row = 0

    def serialize(self):
        return int(self)


class MFloat(float):
    def __init__(self, value, suffix=""):
        self.suffix = suffix

    def __new__(cls, value, suffix=""):
        return float.__new__(cls, value)

    def __str__(self):
        return float_to_si(self) + self.suffix

    def __repr__(self):
        return self.__str__()

    def serialize(self):
        return float(self)


class MBool(object):
    def __init__(self, value):
        self.value = bool(value)
        self.dataModel = None
        self.parent = None
        self.row = 0

    def __str__(self):
        return str(self.value)

    def __bool__(self):
        return self.value

    def serialize(self):
        return bool(self)


class MString(str):
    def serialize(self):
        return str(self)
