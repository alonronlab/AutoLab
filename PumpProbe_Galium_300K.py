#===============================================================================================
#   Name:           PumpProbe_Galium_300K.py
#   Description:    Automates lab devices
#   Author:         Noam Kovartovsky
#===============================================================================================
#===============================================================================================
#   Python Imports
#===============================================================================================
import os, sys
import argparse
import pandas as pd
import numpy as np
import scipy.constants
import matplotlib.pyplot as plt

import logging
FORMAT = '%(asctime)s @ %(levelname)s --- %(filename)s: %(message)s'
logging.basicConfig(format=FORMAT, stream=sys.stdout, level=logging.INFO)
logger = logging.getLogger(__name__)

#===============================================================================================
#   Solution Imports
#===============================================================================================
import devices.SR860 as sr860
import devices.standa as standa

#===============================================================================================
#   Constants
#===============================================================================================
STANDA_LOCATIONS_IN_MM = np.linspace(start=10, stop=-10, num=100)
LOCKIN_SAMPLE_COUNT_PER_STANDA_LOC = 300
LOCKIN_ALL_SAMPLES_DURATION_IN_SEC = 4
CSV_PATH = r'measurements.csv'

#===============================================================================================
#   Functions
#===============================================================================================
def connect_devices(*devices):
    for dev in devices:
        dev.connect()
        if not dev.is_connected:
            return False

    return True

def close_devices(*devices):
    for dev in devices:
        dev.close()

def write_measurement_to_csv(x, y, xerr='', yerr='', header=False):
    csv_row = {
        't'         :   [x, ],
        't_err'     :   [xerr, ],
        'DR'        :   [y, ],
        'DR err'    :   [yerr, ]
    }

    df = pd.DataFrame(csv_row)
    df.to_csv(CSV_PATH, mode='a', index=False, header=header)

#===============================================================================================
#   Main
#===============================================================================================
def main():
    # initiates all parameters, devices and connections
    lockin_dev = sr860.SR860Device()
    standa_dev = standa.StandaDevice()
    if not connect_devices(lockin_dev, standa_dev):
        return

    lockin_dev.calc_capture_freq(LOCKIN_SAMPLE_COUNT_PER_STANDA_LOC / LOCKIN_ALL_SAMPLES_DURATION_IN_SEC)

    # calculate experiment duration
    exp_duration_in_sec = len(STANDA_LOCATIONS_IN_MM) * LOCKIN_SAMPLE_COUNT_PER_STANDA_LOC / lockin_dev.sample_frequency
    logging.info("Expected experiment duration: %.2f minutes" % (exp_duration_in_sec / 60, ))

    # run experiment
    measurements_x = np.zeros(len(STANDA_LOCATIONS_IN_MM))
    x_std = np.zeros(len(STANDA_LOCATIONS_IN_MM))
    for i, loc in enumerate(STANDA_LOCATIONS_IN_MM):
        # move stage and wait for it to stop moving
        standa_dev.move_stage(loc)

        # take measurements from lockin
        logging.info("measuring location %.2f" % (loc, ))
        samples_x, _, _ = lockin_dev.capture_samples(LOCKIN_SAMPLE_COUNT_PER_STANDA_LOC)
        measurements_x[i] = samples_x.mean()
        x_std[i] = samples_x.std()

        # add csv row
        headers = False if i else True
        t = loc * 2 / scipy.constants.c       # delta time
        write_measurement_to_csv(t, measurements_x[i], yerr=x_std[i], header=headers)

    # plot measurements
    fig, ax = plt.subplots()
    ax.errorbar(x=STANDA_LOCATIONS_IN_MM, y=measurements_x, yerr=x_std, ls='None', marker='o')
    ax.set(xlabel="position [mm]", ylabel="X [V]")
    plt.legend()
    plt.tight_layout()
    plt.show()

    # close all devices and connections
    close_devices(standa_dev, lockin_dev)


if __name__ == '__main__':
    main()