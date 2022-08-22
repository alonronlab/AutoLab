#===============================================================================================
#   Name:           AutoLabDevice.py
#   Description:    The parent device class implementation
#   Author:         Noam Kovartovsky
#===============================================================================================
#===============================================================================================
#   Python Imports
#===============================================================================================


import logging
logger = logging.getLogger(__name__)

#===============================================================================================
#   Solution Imports
#===============================================================================================


#===============================================================================================
#   Constants
#===============================================================================================
INVALID_DEVICE_ID = -1

#===============================================================================================
#   AutoLabDevice
#===============================================================================================
class AutoLabDevice(object):

    def __init__(self):
        super(AutoLabDevice, self).__init__()
        self._is_connected = False

    @property
    def is_connected(self):
        return self._is_connected

    def connect(self):
        raise NotImplementedError()

    def close(self):
        raise NotImplementedError()
