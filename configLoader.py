import os
from schema import TObject, TDict, TUnion, TList, TString, TFloat, TInt, TBool
import json

class ConfigLoader():
    def __init__(self):
        class Configuration(TObject):
            datadir = TString()
            instruments = TDict(TUnion({}))
            record_duration = TFloat()
            record_samples = TInt()
            samples = TList(TString())
            master_instrument = TString()
            flush_datafiles = TBool()

        self.schema = Configuration

    def registerInstrument(self, dtype):
        instrument_dict = self.schema.dtypes['instruments']
        union = instrument_dict.dtype
        union.dtypes[dtype.dtypes['type_'].default] = dtype

    def loadFile(self, fp):
        return self.schema(json.load(fp))

    def loadString(self, value):
        return self.schema(json.loads(value))

    def loadData(self, value):
        return self.schema(value)

    def saveFile(self, fp, data):
        json.dump(data.serialize(), fp, indent=4, separators=(',', ': '))

    def saveString(self, data):
        return json.dumps(data.serialize(), indent=4, separators=(',', ': '))

    def save(self, data):
        return data.serialize()
