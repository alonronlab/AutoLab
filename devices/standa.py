#===============================================================================================
#   Name:           standa.py
#   Description:    standa device implementation
#   Author:         Noam Kovartovsky
#===============================================================================================
#===============================================================================================
#   Python Imports
#===============================================================================================
from ctypes import *
import time
import os
import sys
import platform
import tempfile
import re
import numpy as np

if sys.version_info >= (3, 0):
    import urllib.parse

import logging
logger = logging.getLogger(__name__)

#===============================================================================================
#   Solution Imports
#===============================================================================================
import devices.AutoLabDevice as AutoLabDevice

#===============================================================================================
#   Constants
#===============================================================================================


#===============================================================================================
#   Dependences
#===============================================================================================
# For correct usage of the library libximc,
# you need to add the file pyximc.py wrapper with the structures of the library to python path.
cur_dir = os.path.abspath(os.path.dirname(__file__))  # Specifies the current directory.
ximc_dir = r"C:\Standa SDK\ximc-2.13.5\ximc"  # Formation of the directory name with all dependencies. The dependencies for the examples are located in the ximc directory.
ximc_package_dir = os.path.join(ximc_dir, "crossplatform", "wrappers",
                                "python")  # Formation of the directory name with python dependencies.
sys.path.append(ximc_package_dir)  # add pyximc.py wrapper to python path

# Depending on your version of Windows, add the path to the required DLLs to the environment variable
# bindy.dll
# libximc.dll
# xiwrapper.dll
if platform.system() == "Windows":
    # Determining the directory with dependencies for windows depending on the bit depth.
    arch_dir = "win64" if "64" in platform.architecture()[0] else "win32"  #
    libdir = os.path.join(ximc_dir, arch_dir)
    if sys.version_info >= (3, 8):
        os.add_dll_directory(libdir)
    else:
        os.environ["Path"] = libdir + ";" + os.environ["Path"]  # add dll path into an environment variable

try:
    from pyximc import *
except ImportError as err:
    logger.error(
        "Can't import pyximc module. The most probable reason is that you changed the relative location of the test_Python.py and pyximc.py files. See developers' documentation for details.")
    exit()
except OSError as err:
    # logger.error(err.errno, err.filename, err.strerror, err.winerror) # Allows you to display detailed information by mistake.
    if platform.system() == "Windows":
        if err.winerror == 193:  # The bit depth of one of the libraries bindy.dll, libximc.dll, xiwrapper.dll does not correspond to the operating system bit.
            logger.error(
                "Err: The bit depth of one of the libraries bindy.dll, libximc.dll, xiwrapper.dll does not correspond to the operating system bit.")
            # logger.error(err)
        elif err.winerror == 126:  # One of the library bindy.dll, libximc.dll, xiwrapper.dll files is missing.
            logger.error("Err: One of the library bindy.dll, libximc.dll, xiwrapper.dll is missing.")
            logger.error(
                "It is also possible that one of the system libraries is missing. This problem is solved by installing the vcredist package from the ximc\\winXX folder.")
            # logger.error(err)
        else:  # Other errors the value of which can be viewed in the code.
            logger.error(err)
        logger.error(
            "Warning: If you are using the example as the basis for your module, make sure that the dependencies installed in the dependencies section of the example match your directory structure.")
        logger.error("For correct work with the library you need: pyximc.py, bindy.dll, libximc.dll, xiwrapper.dll")
    else:
        logger.error(err)
        logger.error(
            "Can't load libximc library. Please add all shared libraries to the appropriate places. It is decribed in detail in developers' documentation. On Linux make sure you installed libximc-dev package.\nmake sure that the architecture of the system and the interpreter is the same")
    exit()

# variable 'lib' points to a loaded library
# note that ximc uses stdcall on win
logger.info("Library loaded")

sbuf = create_string_buffer(64)
lib.ximc_version(sbuf)
logger.info("Library version: " + sbuf.raw.decode().rstrip("\0"))

#===============================================================================================
#   StandaDevice
#===============================================================================================
class StandaDevice(AutoLabDevice.AutoLabDevice):

    def __init__(self, test_device=False):
        super(StandaDevice, self).__init__()
        self._flag_virtual = False
        self.device_id = AutoLabDevice.INVALID_DEVICE_ID
        self.position = 0
        self.test_device = test_device

    def is_connected(self):
        return self._is_connected and not self._flag_virtual

    def move_stage(self, position, calibration=40000, wait=1000):
        """
        Moves the delay stage to position given in mm.
        The calibration of 40000 steps per mm is taken from the initial value in the STANDA software
        and needs to be confirmed. After moving it will wait for wait (ms)
        """
        if not self.is_connected:
            logger.info("Standa device is not connected. Cannot move stage.")
            return

        logger.info(f"Moving stage to {position:.2f}")
        number = np.round(position*calibration)
        number = int(number)

        result = lib.command_move(self.device_id, number, 0)
        result = lib.command_wait_for_stop(self.device_id, wait)

        self.position = position

    def connect(self):

        # Set bindy (network) keyfile. Must be called before any call to "enumerate_devices" or "open_device" if you
        # wish to use network-attached controllers. Accepts both absolute and relative paths, relative paths are resolved
        # relative to the process working directory. If you do not need network devices then "set_bindy_key" is optional.
        # In Python make sure to pass byte-array object to this function (b"string literal").
        result = lib.set_bindy_key(os.path.join(ximc_dir, "win32", "keyfile.sqlite").encode("utf-8"))
        if result != Result.Ok:
            lib.set_bindy_key("keyfile.sqlite".encode("utf-8")) # Search for the key file in the current directory.

        # This is device search and enumeration with probing. It gives more information about devices.
        probe_flags = EnumerateFlags.ENUMERATE_PROBE + EnumerateFlags.ENUMERATE_NETWORK
        enum_hints = b"addr="
        # enum_hints = b"addr=" # Use this hint string for broadcast enumerate
        devenum = lib.enumerate_devices(probe_flags, enum_hints)
        logger.debug("standa device enum handle: " + repr(devenum))
        logger.debug("standa device enum handle type: " + repr(type(devenum)))

        dev_count = lib.get_device_count(devenum)
        logger.debug("standa device count: " + repr(dev_count))

        controller_name = controller_name_t()
        for dev_ind in range(0, dev_count):
            enum_name = lib.get_device_name(devenum, dev_ind)
            result = lib.get_enumerate_device_controller_name(devenum, dev_ind, byref(controller_name))
            if result == Result.Ok:
                logger.debug("Enumerated standa device #{} name (port name): ".format(dev_ind) + repr(enum_name) + ". Friendly name: " + repr(controller_name.ControllerName) + ".")

        open_name = None
        if dev_count > 0:
            open_name = lib.get_device_name(devenum, 0)
        elif sys.version_info >= (3,0):
            # use URI for virtual device when there is new urllib python3 API
            tempdir = tempfile.gettempdir() + "/testdevice.bin"
            if os.altsep:
                tempdir = tempdir.replace(os.sep, os.altsep)
            # urlparse build wrong path if scheme is not file
            uri = urllib.parse.urlunparse(urllib.parse.ParseResult(scheme="file", \
                    netloc=None, path=tempdir, params=None, query=None, fragment=None))
            open_name = re.sub(r'^file', 'xi-emu', uri).encode()
            self._flag_virtual = 1
            logger.info("The real controller is not found or busy with another app.")
            logger.info("The virtual controller is opened to check the operation of the library.")
            logger.info("If you want to open a real controller, connect it or close the application that uses it.")
            return

        if not open_name:
            return

        if type(open_name) is str:
            open_name = open_name.encode()

        logger.info("Open standa device " + repr(open_name))
        self.device_id = lib.open_device(open_name)
        logger.info("standa device id: " + repr(self.device_id))

        if self.test_device:
            self._test_all()

        self._is_connected = True

    def close(self):
        if not self.is_connected:
            return

        logger.info("\nClosing standa device")
        # The device_t device parameter in this function is a C pointer, unlike most library functions that use this parameter
        lib.close_device(byref(cast(self.device_id, POINTER(c_int))))
        self._is_connected = False


    #===============================================================================================
    #   Test Functions
    #===============================================================================================
    def _test_info(self):
        logger.debug("\nGet device info")
        x_device_information = device_information_t()
        result = lib.get_device_information(self.device_id, byref(x_device_information))
        logger.debug("Result: " + repr(result))
        if result == Result.Ok:
            logger.debug("Device information:")
            logger.debug(" Manufacturer: " +
                    repr(string_at(x_device_information.Manufacturer).decode()))
            logger.debug(" ManufacturerId: " +
                    repr(string_at(x_device_information.ManufacturerId).decode()))
            logger.debug(" ProductDescription: " +
                    repr(string_at(x_device_information.ProductDescription).decode()))
            logger.debug(" Major: " + repr(x_device_information.Major))
            logger.debug(" Minor: " + repr(x_device_information.Minor))
            logger.debug(" Release: " + repr(x_device_information.Release))

    def _test_status(self):
        logger.debug("\nGet status")
        x_status = status_t()
        result = lib.get_status(self.device_id, byref(x_status))
        logger.debug("Result: " + repr(result))
        if result == Result.Ok:
            logger.debug("Status.Ipwr: " + repr(x_status.Ipwr))
            logger.debug("Status.Upwr: " + repr(x_status.Upwr))
            logger.debug("Status.Iusb: " + repr(x_status.Iusb))
            logger.debug("Status.Flags: " + repr(hex(x_status.Flags)))

    def _test_set_microstep_mode_256(self):
        logger.debug("\nSet microstep mode to 256")
        # Create engine settings structure
        eng = engine_settings_t()
        # Get current engine settings from controller
        result = lib.get_engine_settings(self.device_id, byref(eng))
        # Print command return status. It will be 0 if all is OK
        logger.debug("Read command result: " + repr(result))
        # Change MicrostepMode parameter to MICROSTEP_MODE_FRAC_256
        # (use MICROSTEP_MODE_FRAC_128, MICROSTEP_MODE_FRAC_64 ... for other microstep modes)
        eng.MicrostepMode = MicrostepMode.MICROSTEP_MODE_FRAC_256
        # Write new engine settings to controller
        result = lib.set_engine_settings(self.device_id, byref(eng))
        # Print command return status. It will be 0 if all is OK
        logger.debug("Write command result: " + repr(result))

    def _test_set_speed(self, speed=1000):
        logger.debug("\nSet speed")
        # Create move settings structure
        mvst = move_settings_t()
        # Get current move settings from controller
        result = lib.get_move_settings(self.device_id, byref(mvst))
        # Print command return status. It will be 0 if all is OK
        logger.debug("Read command result: " + repr(result))
        logger.debug("The speed was equal to {0}. We will change it to {1}".format(mvst.Speed, speed))
        # Change current speed
        mvst.Speed = int(speed)
        # Write new move settings to controller
        result = lib.set_move_settings(self.device_id, byref(mvst))
        # Print command return status. It will be 0 if all is OK
        logger.debug("Write command result: " + repr(result))

    def _test_all(self):
        logger.info("Testing standa device")
        self._test_info()
        self._test_status()
        self._test_set_microstep_mode_256()
        self._test_set_speed()
        print('\n\n')

#===============================================================================================
#   Functions
#==============================================================================================