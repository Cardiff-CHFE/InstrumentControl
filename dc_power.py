from instrument import Instrument
import scpi
from scpi import onoff
import math
import numpy as np
import time
import copy

class DcPower(Instrument):
    def __init__(self, resource):
        super().__init__()
        self.res = scpi.Wrapper(resource)
        self.cfg = {}

    @staticmethod
    def match_device(devname):
        model = devname.split(",")[1].strip()
        return model == "XXXXXX" or model == "YYYYYY"

    def setup(self, config):
        """Override this to initialize the instrument"""

    def sample(self, elapsed):
        """Override this to acquire/write a sample"""
        return []

    def cleanup(self):
        """Override this to close the instrument cleanly"""

    def get_headers(self):
        """Override this to return a list of logfile headers"""
        return []

    def format_sample(self, sample):
        """Override this for convert samples into a list for logging"""
        return []
