from schema import TBool, TDict, TFloat, TObject, TString, TInt

class Config(TObject):
    type_ = TString("visaScript")
    resource = TString()
    script = TString()
