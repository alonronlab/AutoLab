#===============================================================================================
#   Name:           SR860.py
#   Description:    SR860 device (lock-in) implementation
#   Author:         Noam Kovartovsky
#===============================================================================================
#===============================================================================================
#   Python Imports
#===============================================================================================
import time
import numpy as np
from qcodes.instrument_drivers.stanford_research.SR860 import SR860  # the lock-in amplifier

import logging
logger = logging.getLogger(__name__)

#===============================================================================================
#   Solution Imports
#===============================================================================================
import devices.AutoLabDevice as AutoLabDevice

#===============================================================================================
#   Constants
#===============================================================================================
LOCKIN_SERIAL_PORT = "USB0::0xB506::0x2000::004529::INSTR"

#===============================================================================================
#   Lockin class
#===============================================================================================
class SR860Device(AutoLabDevice.AutoLabDevice):

    def __init__(self):
        super(SR860Device, self).__init__()
        self.lockin = None
        self._sample_frequency = 0

    def connect(self):
        self.lockin = SR860("lockin", LOCKIN_SERIAL_PORT)
        self._is_connected = True

    def close(self):
        self._is_connected = False

    @property    
    def sample_frequency(self):
        return self._sample_frequency

    def calc_capture_freq(self, desired_capture_rate):
        if not self.is_connected:
            logger.error("SR860 device is not connected. Cannot get capture frequency.")
            return None

        chosen_freq = None
        for freq in self.lockin.buffer.available_frequencies:
            if desired_capture_rate >= freq:
                chosen_freq = freq
                break

        self._sample_frequency = chosen_freq

    def capture_samples(self, samples_count):
        if not self.is_connected:
            logger.error("SR860 device is not connected. Cannot capture samples.")
            return None, None, None

        if not self.sample_frequency:
            logger.error("Sample frequency is not calculated for SR860 device. Cannot capture samples.")
            return None, None, None

        time_interval = 1 / self.sample_frequency
        x = np.zeros(samples_count)
        y = np.zeros(samples_count)
        r = np.zeros(samples_count)

        for i in range(samples_count):
            data = self.lockin.get_data_channels_dict()
            x[i] = data['X']
            y[i] = data['Y']
            r[i] = data['R']
            time.sleep(time_interval)

        return x, y, r
