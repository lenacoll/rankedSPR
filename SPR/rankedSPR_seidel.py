from os.path import exists
from unlabelled_rankedspr_distances import *
from rankedspr_distances import *
import time
from numpy.ctypeslib import ndpointer
import numpy as np
import ctypes
__author__ = 'Lena Collienne'
# Compute distance matrix for rankedSPR graph (from adjacency matrix, using SEIDEL implementation from RNNI_code package)
from pickle import FALSE
import sys

sys.path.append('../seidel/')


_seidel = ctypes.CDLL("../seidel/libseidel.so")
_seidel.test_function.argtypes = (ndpointer(ctypes.c_int,
                                            flags="C_CONTIGUOUS"),
                                  ctypes.c_int32)
_seidel.seidel.argtypes = (ndpointer(ctypes.c_int,
                                     flags="C_CONTIGUOUS"), ctypes.c_int32)
_seidel.seidel_recursive.argtypes = (ndpointer(ctypes.c_int,
                                               flags="C_CONTIGUOUS"),
                                     ctypes.c_int32, ctypes.c_int32)


def rankedspr_seidel(n, hspr=False):
    # compute distance matrix for RSPR (or HSPR if HSPR=0), for trees on n leaves
    print('number of leaves:', n)
    AI = rankedSPR_adjacency(n, hspr)
    A = np.ascontiguousarray(AI[0], dtype=np.int32)
    time1 = time.time()
    _seidel.seidel(A, A.shape[0])
    if (hspr == True):
        np.save('output/distance_matrix_' + str(n) + '_leaves_hspr', A)
    else:
        np.save('output/distance_matrix_' + str(n) + '_leaves', A)
    time2 = time.time()
    print("C Seidel took {:.3f}ms".format((time2 - time1) * 1000.0))
    print("diameter: ", np.amax(A))


def rankedspr_wo_RNNI_seidel(n):
    # compute distance matrix for RSPR without RNNI moves, for trees on n leaves
    print('number of leaves:', n)
    AI = rankedSPR_wo_RNNI_adjacency(n)
    A = np.ascontiguousarray(AI[0], dtype=np.int32)
    time1 = time.time()
    _seidel.seidel(A, A.shape[0])
    np.save('output/wo_RNNI_distance_matrix_' + str(n) + '_leaves', A)
    time2 = time.time()
    print("C Seidel took {:.3f}ms".format((time2 - time1) * 1000.0))
    print("diameter: ", np.amax(A))


def unlabelled_ranked_spr_seidel(n, hspr=True):
    # compute distance matrix for RSPR (or HSPR if HSPR == True), for trees on n leaves
    print('number of leaves:', n)
    AI = unlabelled_rankedSPR_adjacency(n, hspr)
    A = np.ascontiguousarray(AI[0], dtype=np.int32)
    time1 = time.time()
    _seidel.seidel(A, A.shape[0])
    if (hspr == True):
        np.save('output/unlabelled_distance_matrix_' + str(n) + '_leaves_hspr',
                A)
    else:
        np.save('output/unlabelled_distance_matrix_' + str(n) + '_leaves', A)
    time2 = time.time()
    print("C Seidel took {:.3f}ms".format((time2 - time1) * 1000.0))
    print("diameter: ", np.amax(A))
