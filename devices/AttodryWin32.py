import argparse
import ctypes

###Load Attodry800 dll to memory
LIB_ATTODRY800_PATH = r"C:\Users\Ron's Optics Lab\Desktop\AttodryDLL\attoDRYLib.dll"
attodll = ctypes.CDLL(LIB_ATTODRY800_PATH)

parser = argparse.ArgumentParser()
parser.add_argument("-g", "--get", action="store_true", help="get temperature")
parser.add_argument("-s", "--set", type=float, help="sets temperature to value (kelvin)")
args = parser.parse_args()

if args.get:
	print("Get")
elif args.set:
	print("Set %.2f" % (args.set, ))
