from instrument import Instrument, runlater, InstrumentError
from datetime import datetime, timezone, timedelta
import queue

UNEXPECTED_CLOSE_MSG = "Serial port closed unexpectedly"

class Driver(Instrument):
    def __init__(self, config):
        super().__init__()
        self.config = config

    def setup(self):
        import serial
        self.res = serial.Serial(self.config.serialPort, timeout=3.0)

    def sample(self):
        sampletime = datetime.now(timezone.utc)

        if self.read_bytes(1)[0] != 0x02:
            return None

        
        if self.config.model == '1316':
            ret = self.read_bytes(1)
            ch0 = self.read_sample()
            #TODO: Allow Kelvin and farenheight modes. Kelvin 0x02, Farenheight 0x03
            if ret[0] != 0x00:
                ch0 = 0.0
            ret = self.read_bytes(1)
            ch1 = self.read_sample()
            if ret[0] != 0x00:
                ch1 = 0.0
            if self.read_bytes(1)[0] != 0x00:
                return None
        else:
            ch0 = self.read_sample()
            ch1 = self.read_sample()

        if self.read_bytes(1)[0] != 0x03:
            return None

        return sampletime, [ch0, ch1]

    def read_bytes(self, count=1):
        data = self.res.read(count)
        if len(data) != count:
            raise InstrumentError(UNEXPECTED_CLOSE_MSG)
        return data

    def read_sample(self):
        data = self.read_bytes(2)
        return (data[1] | ((data[0] & 0x3f)<<8))*0.1

    def cleanup(self):
        self.res.close()

    def get_headers(self):
        if self.config.model == '1316':
            return ["Temperature1 (C)", "Temperature2 (C)"]
        else:
            return ["Temperature (C)", "Relative Humidity (%)"]

    def format_sample(self, sample):
        return sample