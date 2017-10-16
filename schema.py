import collections

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
        if value is None:
            value = {}
        if isinstance(value, MDict):
            if value.dtype != self.dtype:
                raise ValueError("Invalid dictionary type")
            return value
        return MDict(self.dtype, value)

    def __eq__(self, other):
        return type(other) == type(self) and other.dtype == self.dtype


class TList(T):
    def __init__(self, dtype):
        self.dtype = dtype

    def __call__(self, value=None):
        if value is None:
            value = []
        if isinstance(value, MList):
            if value.dtype != self.dtype:
                raise ValueError("Invalid list type")
            return value
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
    # TODO Implement bounds checking
    def __call__(self, value=0):
        return MInt(value)

    def __eq__(self, other):
        return type(other) == type(self)


class TFloat(T):
    # TODO Implement bounds checking
    def __call__(self, value=0.0):
        return MFloat(value)

    def __eq__(self, other):
        return type(other) == type(self)


class TBool(T):
    # TODO Implement bounds checking
    def __call__(self, value=False):
        return MBool(value)

    def __eq__(self, other):
        return type(other) == type(self)


class TString(T):
    # TODO Implement bounds checking
    def __call__(self, value=""):
        return MString(value)

    def __eq__(self, other):
        return type(other) == type(self)


class BaseCollection(object):
    def __init__(self, items=None):
        self._model = None
        self._data = []
        if items is not None:
            for key, value in items:
                self.addChild(value, key)

    def dtypeForRow(self, row):
        """Override this to get the data type of a row"""
        raise NotImplementedError()

    def keyForRow(self, row):
        """Override this to generate a key for a row"""
        raise NotImplementedError()

    def rowForKey(self, key):
        for i, (row, _) in enumerate(self._data):
            if row == key:
                return i
        raise KeyError()

    def updateRowKey(self, row):
        """Override this to update keys of rows that have moved"""
        return None

    def childCount(self):
        return len(self._data)

    def child(self, row):
        return self._data[row]

    def children(self):
        for row in self._data:
            yield row

    def setChild(self, row, value):
        self._data[row][1] = self._newChild(row, value)
        try:
            self.model.updateChild(self, row)
        except AttributeError:
            pass

    def setChildKey(self, row, value):
        self._data[row][0] = str(value)
        try:
            self.model.updateChildKeys(self, row, 1)
        except AttributeError:
            pass

    def addChild(self, value, key=None):
        self.insertChild(len(self._data), value, key)

    def insertChild(self, row, value, key=None):
        try:
            self.model.beginInsertChildren(self, row, 1)
        except AttributeError:
            pass

        if key is None:
            key = self.keyForRow(row)
        else:
            key = str(key)
        self._data.insert(row, (key, self._newChild(row, value)))

        try:
            self.model.endInsertChildren(self)
        except AttributeError:
            pass

        self._updateKeys(row, len(self._data))

    def insertChildren(self, row, count):
        try:
            self.model.beginInsertChildren(self, row, count)
        except AttributeError:
            pass

        for i in range(row, row+count):
            key = self.keyForRow(i)
            self._data.insert(i, (key, self._newChild(i)))

        try:
            self.model.endInsertChildren(self)
        except AttributeError:
            pass

        self._updateKeys(row+count, len(self._data))

    def removeChildren(self, row, count):
        try:
            self.model.beginRemoveChildren(self, row, count)
        except AttributeError:
            pass

        for i in range(count):
            del self._data[row]

        try:
            self.model.endRemoveChildren(self)
        except AttributeError:
            pass

        self._updateKeys(row, len(self._data))

    def _newChild(self, row, value=None):
        if value is None:
            value = self.dtypeForRow(row)()
        else:
            value = self.dtypeForRow(row)(value)
        value.parent = self
        value.row = row
        value.model = self.model
        return value

    def _updateKeys(self, start, end):
        keysChanged = False
        for i in range(start, end):
            newKey = self.updateRowKey(i)
            if newKey is not None:
                self._data[i][0] = newKey
                keysChanged = True
        if keysChanged:
            try:
                self.model.updateChildKeys(self, start, end-start)
            except AttributeError:
                pass

    @property
    def model(self):
        return self._model

    @model.setter
    def model(self, model):
        self._model = model
        for _, value in self._data:
            value.model = model


class PropertyInternal:
    __slots__ = ['dtype', 'name', 'row']

    def __init__(self, row):
        self.row = row

    def __get__(self, instance, owner=None):
        if instance is None:
            return self
        return instance.child(self.row)[1]

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
        self._model = None
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
                        items.append(key, data[key])
                        keys.remove(key)
                    except KeyError:
                        items.append(key, None)
                super().__init__(items)
                # Store unused keys in the extras dict
                for key in keys:
                    self._extras[key] = data[key]

    def serialize(self):
        data = self._extras.copy()
        for key, value in self.children():
            data[key] = value.serialize()
        return data

    def dtypeForRow(self, row):
        return list(self.dtypes.values())[row]

    def setChildKey(self, row, value):
        raise RuntimeError("Cannot change TObject keys")

    def insertChild(self, row, value, key=None):
        raise RuntimeError("Cannot insert into TObject")

    def insertChildren(self, row, count):
        raise RuntimeError("Cannot insert into TObject")

    def removeChildren(self, row, count):
        raise RuntimeError("Cannot remove from TObject")


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
            except KeyError:
                return key

    def __setitem__(self, key, value):
        try:
            row = self.rowForKey(key)
            self.setChild(row, value)
        except KeyError:
            super().addChild(value, key)

    def __getitem__(self, key):
        row = self.rowForKey(key)
        return self.child(row)[1]

    def __delitem__(self, key):
        row = self.rowForKey(key)
        self.removeChildren(row, 1)

    def __iter__(self):
        for row in self.children():
            yield row[0]

    def items():
        """Optional, but improves efficiency of iteration"""
        return self.children()

    def values():
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
            self.rowForKey(value)
            raise ValueError("Key already exists")
        except KeyError:
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


class MList(BaseCollection, collections.MutableSequence):
    def __init__(self, dtype, items=None):
        self.dtype = dtype
        if items is not None:
            items = enumerate(items, start=1)
        super().__init__(items)

    def dtypeForRow(self, row):
        return self.dtype

    def keyForRow(self, row):
        return str(row + 1)

    def updateRowKey(self, row):
        return str(row+1)

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

    def setChildKey(self, row, value):
        """List keys cannot be changed"""
        pass

    def insertChild(self, row, value, key=None):
        """Ignore the key and let the list choose it's own"""
        super().insertChild(row, value)


class MInt(int):
    def __init__(self, *args, **kwargs):
        self.model = None
        self.parent = None
        self.row = 0

    def serialize(self):
        return int(self)


class MFloat(float):
    def __init__(self, *args, **kwargs):
        self.model = None
        self.parent = None
        self.row = 0

    def serialize(self):
        return float(self)


class MBool(bool):
    def __init__(self, *args, **kwargs):
        self.model = None
        self.parent = None
        self.row = 0

    def serialize(self):
        return bool(self)


class MString(str):
    def __init__(self, *args, **kwargs):
        self.model = None
        self.parent = None
        self.row = 0

    def serialize(self):
        return str(self)
