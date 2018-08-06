from schema import TBool, TDict, TFloat, TObject, TString, TInt

class Config(TObject):
    type_ = TString("datalogger")
    serialPort = TString()
    model = TString("1365")
