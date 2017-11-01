from schema import TBool, TDict, TFloat, TObject, TString, TInt


class Segment(TObject):
    f0 = TFloat(2.5e9, suffix="Hz")
    span = TFloat(1e6, suffix="Hz")
    points = TInt(201)
    ifbw = TFloat(1e3, suffix="Hz")
    power = TFloat(suffix="dBm")


class Config(TObject):
    type_ = TString("vna")
    model = TString()
    resource = TString()
    track_frequency = TBool(True)
    track_span = TBool()
    use_markers = TBool()
    bandwidth_factor = TFloat(4.0)
    segments = TDict(Segment)
