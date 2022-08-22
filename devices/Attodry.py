#===============================================================================================
#   Name:           Attodry.py
#   Description:    Attodry device (Cryostat) implementation
#   Author:         Noam Kovartovsky
#===============================================================================================
#===============================================================================================
#   Python Imports
#===============================================================================================
import os, sys
import subprocess

#===============================================================================================
#   Solution Imports
#===============================================================================================
import devices.AutoLabDevice as AutoLabDevice

#===============================================================================================
#   Constants
#===============================================================================================
PYTHON32BIT = r"C:\Users\Ron's Optics Lab\AppData\Local\Programs\Python\Python39-32\python.exe"
ATTOLIB_PATH = r"C:\Users\Ron's Optics Lab\Desktop\AutoLab\devices\AttodryWin32.py"

#===============================================================================================
#   Lockin class
#===============================================================================================
class CryostatDevice(AutoLabDevice.AutoLabDevice):

    def __init__(self):
        super(CryostatDevice, self).__init__()

    def connect(self):
    	"""
    	Handled in AttodryWin32
    	"""
        pass

    def close(self):
    	"""
    	Handled in AttodryWin32
    	"""
        pass

	def get_temperature(self):
		subprocess.call([PYTHON32BIT, ATTOLIB_PATH, "--get"])

	def set_temperature(self, tempInKelvin):
		subprocess.call([PYTHON32BIT, ATTOLIB_PATH, "--set", str(tempInKelvin)])

