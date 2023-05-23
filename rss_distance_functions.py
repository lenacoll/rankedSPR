__author__ = 'Lena Collienne'

import sys
from ctypes import *
sys.path.append('treeOclock')
from tree_functions import *

lib = CDLL(f'{os.path.dirname(os.path.realpath(__file__))}/rss_distance.so')


rss_distance = lib.rss_distance
rss_distance.argtypes = [POINTER(TREE), POINTER(TREE)]
rss_distance.restype = c_long
