__author__ = 'Lena Collienne'
# Computing the rankedSPR graph to test algorithms for computing distances for trees on a small number of leaves
from itertools import count
from platform import architecture
import sys

from analyse_distance_distribution import read_newick_tree_file
sys.path.append('treeOclock/')
sys.path.append('treeOclock/dct_parser/')

import ctypes
import math
import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import copy as cp
import random
import re
from treeOclock.dct_parser.tree_io import *
from treeOclock import *
from simulate_trees import *
from os.path import exists
from numpy.ctypeslib import ndpointer


_seidel = ctypes.CDLL("./libseidel.so")
_seidel.test_function.argtypes = (ndpointer(ctypes.c_int, flags="C_CONTIGUOUS"), ctypes.c_int32)
_seidel.seidel.argtypes = (ndpointer(ctypes.c_int, flags="C_CONTIGUOUS"), ctypes.c_int32)
_seidel.seidel_recursive.argtypes = (ndpointer(ctypes.c_int, flags="C_CONTIGUOUS"), ctypes.c_int32, ctypes.c_int32)


# Compute the adjacency matrix of the rankedSPR graph
# If hspr = 1, compute matrix for rankedSPR graph, otherwise for HSPR graph
def rankedSPR_adjacency(num_leaves, hspr = 1):
    num_trees = math.factorial(num_leaves - 1) * math.factorial(num_leaves) / (2**(num_leaves - 1))
    tree_index = dict() # dict containing trees as keys (as strings of cluster representation) and their index in adjacency matrix as values.
    index = 0 # Index of the last added tree in tree_index
    not_visited = [] # Save the trees that are already generated, but have not been added to adjacency matrix, in list
    visited = [] # Save the trees that have already been used, i.e. their 1-neighbourhoods have already been considered
    start_tree = identity_caterpillar(num_leaves)
    start_tree_str = tree_to_cluster_string(start_tree)
    tree_index[start_tree_str] = 0
    current_tree = start_tree
    visited.append(start_tree_str)
    # not_visited.append(start_tree_str)
    index += 1

    # adjacency matrix, initialised to only have 0s:
    adj = np.zeros((int(num_trees), int(num_trees)))

    # Fill tree_index with all trees on num_leaves leaves by going through lots of one-neighbourhoods, starting at start_tree:
    # Note that this is VERY inefficient! It is only kind of quick for up to 7 leaves!
    # We could do this a lot more efficient if we used the coalescent process.
    while len(visited) < num_trees:
        neighbourhood = all_spr_neighbourhood(current_tree, hspr)
        current_tree_str = tree_to_cluster_string(current_tree)

        for i in range(0,neighbourhood.num_trees):
            tree = neighbourhood.trees[i]
            tree_str = tree_to_cluster_string(tree)
            if tree_str not in tree_index:
                tree_index[tree_str] = index
                # Add 1 to adjacency matrix:
                index += 1
            adj[tree_index[current_tree_str],tree_index[tree_str]]=1
            adj[tree_index[tree_str], tree_index[current_tree_str]]=1

        # Randomly take the tree for the next iteration from the list of neighbours
        next_tree = sim_coal(num_leaves,1).trees[0]
        # next_tree = neighbourhood.trees[next_tree_index]
        next_tree_str = tree_to_cluster_string(next_tree)
        # We might get stuck somewhere in space where we can only escape by picking a new (random) starting tree
        while (next_tree_str in visited):
            next_tree = sim_coal(num_leaves,1).trees[0] # randomly choose the next tree for which we will compute the one-neighbourhood
            next_tree_str = tree_to_cluster_string(next_tree)
        visited.append(next_tree_str)
        if next_tree_str not in tree_index:
            tree_index[next_tree_str] = index
            index += 1
        current_tree = next_tree # update current_tree

    # Save tree dict in file:
    # open file for writing
    if hspr == 0:
        f = open("SPR/tree_dict_" + str(num_leaves) + "_leaves_hspr.txt","w")
    else:
        f = open("SPR/tree_dict_" + str(num_leaves) + "_leaves.txt","w")

    # write file
    for key in tree_index:
        f.write(str(tree_index[key]) + " " +str(key))
        f.write("\n")

    # close file
    f.close()

    # Save adjacency matrix in file
    if hspr ==1:
        if not exists('SPR/adj_matrix_%s_leaves.npy' %num_leaves):
            np.save("SPR/adj_matrix_" + str(num_leaves) + "_leaves.npy", adj)
    else:
        if not exists('SPR/adj_matrix_%s_leaves_hspr.npy' %num_leaves):
            np.save("SPR/adj_matrix_" + str(num_leaves) + "_leaves_hspr.npy", adj)
    return(adj, tree_index)


# Compute the adjacency matrix of the rankedSPR graph without RNNI moves
def rankedSPR_wo_RNNI_adjacency(num_leaves):
    num_trees = math.factorial(num_leaves - 1) * math.factorial(num_leaves) / (2**(num_leaves - 1))
    tree_index = dict() # dict containing trees as keys (as strings of cluster representation) and their index in adjacency matrix as values.
    index = 0 # Index of the last added tree in tree_index
    visited = [] # Save the trees that have already been used, i.e. their 1-neighbourhoods have already been considered
    start_tree = identity_caterpillar(num_leaves)
    start_tree_str = tree_to_cluster_string(start_tree)
    tree_index[start_tree_str] = 0
    current_tree = start_tree
    visited.append(start_tree_str)
    index += 1

    # adjacency matrix, initialised to only have 0s:
    adj = np.zeros((int(num_trees), int(num_trees)))

    # Fill tree_index with all trees on num_leaves leaves by going through lots of one-neighbourhoods, starting at start_tree:
    # Note that this is VERY inefficient! It is only kind of quick for up to 7 leaves!
    # We could do this a lot more efficient if we used the coalescent process.
    while len(visited) < num_trees:
        neighbourhood = all_spr_neighbourhood(current_tree, 0)
        current_tree_str = tree_to_cluster_string(current_tree)

        rnni_neighbours = rnni_neighbourhood(current_tree)

        for i in range(0,neighbourhood.num_trees):
            tree = neighbourhood.trees[i]
            ignore = False # decide whether we ignore this neighbour, because it is rnni neighbour
            for j in range(0,rnni_neighbours.num_trees):
                if same_tree(tree,rnni_neighbours.trees[j])==0:
                    ignore = True
                    break
            if ignore == False:
                tree_str = tree_to_cluster_string(tree)
                if tree_str not in tree_index:
                    tree_index[tree_str] = index
                    # Add 1 to adjacency matrix:
                    index += 1
                adj[tree_index[current_tree_str],tree_index[tree_str]]=1
                adj[tree_index[tree_str], tree_index[current_tree_str]]=1

        # Randomly take the tree for the next iteration from the list of neighbours
        next_tree = sim_coal(num_leaves,1).trees[0]
        # next_tree = neighbourhood.trees[next_tree_index]
        next_tree_str = tree_to_cluster_string(next_tree)
        # We might get stuck somewhere in space where we can only escape by picking a new (random) starting tree
        while (next_tree_str in visited):
            next_tree = sim_coal(num_leaves,1).trees[0] # randomly choose the next tree for which we will compute the one-neighbourhood
            next_tree_str = tree_to_cluster_string(next_tree)
        visited.append(next_tree_str)
        if next_tree_str not in tree_index:
            tree_index[next_tree_str] = index
            index += 1
        current_tree = next_tree # update current_tree

    # Save tree dict in file:
    # open file for writing
    f = open("SPR/wo_RNNI_tree_dict_" + str(num_leaves) + "_leaves_hspr.txt","w")

    # write file
    for key in tree_index:
        f.write(str(tree_index[key]) + " " +str(key))
        f.write("\n")

    # close file
    f.close()

    # Save adjacency matrix in file
    if not exists('SPR/wo_RNNI_adj_matrix_%s_leaves.npy' %num_leaves):
        np.save("SPR/wo_RNNI_adj_matrix_" + str(num_leaves) + "_leaves.npy", adj)
    return(adj, tree_index)


def read_distance_matrix(num_leaves, hspr=1):
    # read distance matrix and corresponding trees and return them as matrix and two dicts (index to tree and tree to index)
    # Read distance matrix
    if hspr == 1:
        d = np.load('SPR/distance_matrix_' + str(num_leaves) + '_leaves.npy')
        f = open('SPR/tree_dict_' + str(num_leaves) + '_leaves.txt', 'r')
    elif hspr ==0:
        d = np.load('SPR/distance_matrix_' + str(num_leaves) + '_leaves_hspr.npy')
        f = open('SPR/tree_dict_' + str(num_leaves) + '_leaves_hspr.txt', 'r')

    # Put all trees into a dict (note that indices are sorted increasingly in file)
    tree_strings = f.readlines()
    index = 0
    tree_dict = dict()
    tree_index_dict = dict()
    for tree_str in tree_strings:
        tree_str = tree_str.split("'")[1]
        tree_dict[tree_str]=index
        tree_index_dict[index]=tree_str
        index += 1
    return(d, tree_dict, tree_index_dict)


def symmetric_child_cluster_diff(tree1, tree2):
    # Let A_i and B_i be the clusters induces by the children of the node of rank i in tree1 and C_i and D_i those clusters in tree2
    # This function computes the sum of min(|A_i \Delta C_i| + |B_i \Delta D_i|, |A_i \Delta D_i| + |B_i \Delta C_i|) for all internal nodes i = 1, ..., n-1
    num_leaves = tree1.num_leaves
    clusters1 = dict() # dict containing ranks as keys and clusters (as sets of leaves) as values
    clusters2 = dict() # dict containing ranks as keys and clusters (as sets of leaves) as values
    # fill cluster dictionaries with singletons for leaves and empty sets for internal nodes:
    for i in range(0, 2*num_leaves):
        if i < num_leaves:
            clusters1[i] = set([i])
            clusters2[i] = set([i])
        else:
            clusters1[i] = set([])
            clusters2[i] = set([])

    # now fill dicts with actual clusters
    for i in range(0, num_leaves): # if we consider all leaves, we get all clusters (bc mrca of all leaves is root)
        # fill cluster1 dictionary
        j = i
        while tree1.tree[j].parent != -1:
            clusters1[tree1.tree[j].parent].add(i)
            j = tree1.tree[j].parent
        # same for clusters of tree2
        j = i
        while tree2.tree[j].parent != -1:
            clusters2[tree2.tree[j].parent].add(i)
            j = tree2.tree[j].parent

    # compute sum of symmetric differences of clusters
    sum = 0
    for i in range(num_leaves, 2*num_leaves-1):
        A = clusters1[tree1.tree[i].children[0]]
        B = clusters1[tree1.tree[i].children[1]]
        C = clusters2[tree2.tree[i].children[0]]
        D = clusters2[tree2.tree[i].children[1]]
        sum += min(len(A.symmetric_difference(C)) + len(B.symmetric_difference(D)), len(A.symmetric_difference(D)) + len(B.symmetric_difference(C)))
        # print(i, A, B, C, D, sum)
    return(sum)


def dist_symmetric_child_cluster_diff(tree1, tree2):
    distance = 0
    current_tree = tree1
    min_diff = symmetric_child_cluster_diff(current_tree, tree2)
    while min_diff > 0:
        distance += 1
        neighbourhood = hspr_neighbourhood(current_tree)
        for i in range(0, neighbourhood.num_trees):
            current_diff = symmetric_child_cluster_diff(neighbourhood.trees[i], tree2)
            if current_diff < min_diff:
                current_tree = neighbourhood.trees[i]
                min_diff= current_diff
        print(tree_to_cluster_string(current_tree), min_diff)
    return distance


def test_dist_symmetric_child_cluster_diff(num_leaves):
    (d,tree_dict, tree_index_dict) = read_distance_matrix(num_leaves, hspr=0)
    print(d, tree_dict, tree_index_dict)

    num_tree_pairs=0
    correct_distance = 0
    for i in range(0,len(d)):
        tree1_str = tree_index_dict[i]
        tree1 = read_from_cluster(tree1_str)
        for j in range(i+1,len(d)):
            num_tree_pairs+=1
            tree2_str = tree_index_dict[j]
            tree2 = read_from_cluster(tree2_str)

            # print("tree1:", tree1_str)
            # print("tree2:", tree2_str)
            approx_dist = dist_symmetric_child_cluster_diff(tree1, tree2)
            actual_dist = d[i][j]
            if (approx_dist == actual_dist):
                correct_distance += 1
            else:
                # if (approx_dist - actual_dist >1):
                print(tree1_str, tree2_str, actual_dist)
                print("approximation:", approx_dist, "actual:", actual_dist)
    print('correct distance:', correct_distance, 'out of', num_tree_pairs)


def test_restricted_neighbourhood_search(num_leaves, num_tree_pairs, hspr = 1):
    # Compute adjacency matrix & distance matrix
    rspr_adj = rankedSPR_adjacency(num_leaves, hspr)
    rspr_distances = np.ascontiguousarray(rspr_adj[0], dtype=np.int32)
    _seidel.seidel(rspr_distances, rspr_distances.shape[0])

    # Now simulate trees to be used to check distance computation
    t_list = sim_coal(num_leaves, 2*num_tree_pairs)
    correct_distance = 0
    for i in range(0,num_tree_pairs):
        tree1_index = rspr_adj[1][tree_to_cluster_string(t_list.trees[i])]
        tree2_index = rspr_adj[1][tree_to_cluster_string(t_list.trees[i+1])]
        # print(tree_to_cluster_string(t_list.trees[i]))
        # print(tree_to_cluster_string(t_list.trees[i+1]))
        # print(rspr_distances[tree1_index][tree2_index], rankedspr_path_restricting_neighbourhood(t_list.trees[i],t_list.trees[i+1]))
        if (rspr_distances[tree1_index][tree2_index] == rankedspr_path_restricting_neighbourhood(t_list.trees[i],t_list.trees[i+1], hspr)):
            correct_distance += 1
        else:
            print("tree1:", tree_to_cluster_string(t_list.trees[i]))
            print("tree2:", tree_to_cluster_string(t_list.trees[i+1]))
            print("correct distance:", rspr_distances[tree1_index][tree2_index], "approximated distance:", rankedspr_path_restricting_neighbourhood(t_list.trees[i],t_list.trees[i+1],hspr))
    print('correct distance:', correct_distance, 'out of', num_tree_pairs)


def test_restricted_neighbourhood_search_caterpillar(num_leaves, num_trees, hspr = 1):
    # Compute adjacency matrix & distance matrix
    rspr_adj = rankedSPR_adjacency(num_leaves, hspr)
    rspr_distances = np.ascontiguousarray(rspr_adj[0], dtype=np.int32)
    _seidel.seidel(rspr_distances, rspr_distances.shape[0])

    # Now simulate trees to be used to check distance computation
    t_list = sim_cat(num_leaves, num_trees)
    ctree = identity_caterpillar(num_leaves)
    correct_distance = 0
    ctree_index = rspr_adj[1][tree_to_cluster_string(ctree)]
    for i in range(0,num_trees):
        tree_index = rspr_adj[1][tree_to_cluster_string(t_list.trees[i])]
        # print(tree_to_cluster_string(t_list.trees[i]))
        # print(tree_to_cluster_string(t_list.trees[i+1]))
        # print(rspr_distances[tree_index][tree2_index], rankedspr_path_restricting_neighbourhood(t_list.trees[i],t_list.trees[i+1]))
        if (rspr_distances[tree_index][ctree_index] == rankedspr_path_restricting_neighbourhood(t_list.trees[i], ctree, hspr)):
            correct_distance += 1
        else:
            print("tree1:", tree_to_cluster_string(t_list.trees[i]))
            print("tree2:", tree_to_cluster_string(ctree))
            print("correct distance:", rspr_distances[tree_index][ctree_index], "approximated distance:", rankedspr_path_restricting_neighbourhood(t_list.trees[i],ctree,hspr))
    print('correct distance:', correct_distance, 'out of', num_trees)


def test_top_down_neighbourhood_search(num_leaves, num_tree_pairs):
    # Compute adjacency matrix & distance matrix
    rspr_adj = rankedSPR_adjacency(num_leaves)
    rspr_distances = np.ascontiguousarray(rspr_adj[0], dtype=np.int32)
    _seidel.seidel(rspr_distances, rspr_distances.shape[0])

    # Now simulate trees to be used to check distance computation
    t_list = sim_coal(num_leaves, 2*num_tree_pairs)
    correct_distance = 0
    for i in range(0,num_tree_pairs):
        tree1_index = rspr_adj[1][tree_to_cluster_string(t_list.trees[i])]
        tree2_index = rspr_adj[1][tree_to_cluster_string(t_list.trees[i+1])]
        # print("tree pair:")
        # print(tree_to_cluster_string(t_list.trees[i]))
        # print(tree_to_cluster_string(t_list.trees[i+1]))
        # print(rspr_distances[tree1_index][tree2_index], rankedspr_path_restricting_neighbourhood(t_list.trees[i],t_list.trees[i+1]))
        if (rspr_distances[tree1_index][tree2_index] == rankedspr_path_top_down_symm_diff(t_list.trees[i],t_list.trees[i+1])):
            correct_distance += 1
        else:
            print("tree1:", tree_to_cluster_string(t_list.trees[i]))
            print("tree2:", tree_to_cluster_string(t_list.trees[i+1]))
            print("correct distance:", rspr_distances[tree1_index][tree2_index], "approximated distance:", rankedspr_path_top_down_symm_diff(t_list.trees[i],t_list.trees[i+1]))
    print('correct distance:', correct_distance, 'out of', num_tree_pairs)


# Very slow and inefficient implementation of BFS for rankedSPR -- only useful for VERY small number of leaves
def rankedspr_bfs(start_tree, dest_tree, hspr=1, rnni = False):
    num_leaves = start_tree.num_leaves
    tree_dict = dict() # save trees (as cluster strings) and an index for each tree as value, so we can recover the path after running BFS (backtracking)
    index_dict = dict() # reverse of tree_dict (indices as keys and trees as values)
    predecessor = []
    to_visit = [] # queue containing next trees to be visited in BFS

    dest_tree_string = tree_to_cluster_string(dest_tree)
    
    # Initialise path?
    current_tree = start_tree

    tree_dict[tree_to_cluster_string(start_tree)] = 0
    index_dict[0] = tree_to_cluster_string(start_tree)
    index = 1 # index of the tree we currently consider (to be put as value for that tree into tree_dict)
    to_visit.append(current_tree)
    found = False # True if we found dest_tree
    # Start BFS
    while found == False:
        current_tree = to_visit.pop(0)
        current_tree_str = tree_to_cluster_string(current_tree)
        neighbours = all_spr_neighbourhood(current_tree,hspr)
        for i in range(0,neighbours.num_trees):
            tree = neighbours.trees[i]
            neighbour_string = tree_to_cluster_string(tree)
            if neighbour_string not in tree_dict:
                if rnni == False or (rnni == True and findpath_distance(neighbours.trees[i], dest_tree) < findpath_distance(current_tree, dest_tree)): # only add neighbour if RNNI dist to dest_tree is smaller than from current_tree to dest_tree (if rnni=True):
                    to_visit.append(tree)
                    tree_dict[neighbour_string] = index
                    index_dict[index]=neighbour_string
                    predecessor.append(tree_dict[current_tree_str])
                    index+=1
            if neighbour_string == dest_tree_string:
                found = True
                break

    # backtracking
    current_index = tree_dict[tree_to_cluster_string(dest_tree)]
    path_indices = [current_index]
    while (predecessor[current_index-1] != 0):
        path_indices.append(predecessor[current_index-1])
        current_index = predecessor[current_index-1]
    path_indices.append(0)
    # now turn path_indices array into path:
    path = []
    for i in range(len(path_indices)-1, -1, -1):
        path.append(index_dict[path_indices[i]])
    return(path)


def test_decreasing_rnni_dist(num_leaves, hspr=1):
    # test if there is always a shortest path between any two trees on num_leaves leaves for which the RNNI distance decreases in every step
    (d, tree_dict, tree_index_dict) = read_distance_matrix(num_leaves, hspr)
    no_rnni_decreasing_path = 0 # number of tree pairs not connected by any path that decreases rnni distance in every step
    for i in range(0, len(d)):
        tree1_str = tree_index_dict[i]
        tree1 = read_from_cluster(tree1_str)
        for j in range(i+1, len(d)):
            tree2_str = tree_index_dict[j]
            tree2 = read_from_cluster(tree2_str)
            if d[i][j] != len(rankedspr_bfs(tree1, tree2, hspr, rnni=True))-1:
                print(tree1_str, tree2_str)
                no_rnni_decreasing_path += 1
    print("Number of tree pairs with no path on which RNNI distance decreases monotonically:", no_rnni_decreasing_path)


# Find the ranks on which moves are performed on shortest path resulting from BFS
def bfs_path_rank_sequence(tree1, tree2):
    path = rankedspr_bfs(tree1, tree2, hspr=0)
    rank_list = []
    rank_count = []
    for i in range(0,len(path)-1):
        # for each move, find the lowest rank for which induced cluster changes -- this is the rank on which the HSPR move happened
        path[i] = str(path[i])
        path[i+1] = str(path[i+1])
        rank = 0
        for j in range(0, len(path[i])-1):
            if path[i][j] == '{':
                rank += 1
            if path[i][j] != path[i+1][j]:
                rank_list.append(rank)
                break
    for i in range(1,tree1.num_leaves-1):
        rank_count.append(rank_list.count(i))
    if max(rank_count) > 3:
        print("There is a rank for which more than one move is needed. The corresponding path is:")
        for tree in path:
            print(tree)
    return(rank_count)


def check_HSPR_moves_per_rank(num_leaves, num_tree_pairs):
    # simulate num_tree_pairs trees and check how moves are distributed across ranks in the trees on shortest path computed by bfs
    for i in range(0,num_tree_pairs):
        tree_list = sim_coal(num_leaves,2) # Simulate a pair of trees instead
        rank_count = bfs_path_rank_sequence(tree_list.trees[0], tree_list.trees[1])
        print(rank_count)


# use own implementation of coalescent to plot ranked SPR distances (HSPR if hspr=0, otherwise (default) RSPR) between coalescent trees (i.e. uniform ranked trees)
def coal_pw_spr_dist(num_leaves, num_tree_pairs, hspr = 1, output_file = '', distances_file = ''):
    # Plotting the distances for num_tree_pairs simulated pairs of trees and save plot (if filehandle given) in output_file
    distances = []

    for i in range(0,int(num_tree_pairs)):
        if i%100 == 0:
            print('iteration', i)
        tree_list = sim_coal(num_leaves,2) # Simulate a pair of trees instead of a list with num_tree trees
        distances.append(len(rankedspr_bfs(tree_list.trees[0], tree_list.trees[1]))-1)
    if distances_file != '':
        np.savetxt(distances_file,  distances, delimiter = ' ')
    # Plot histogram
    d = pd.DataFrame(data=distances)
    upper_bound = max(distances)
    b = np.arange(-.5, upper_bound + 1.5, 1)
    sns.set_theme(font_scale=1.2)
    sns.histplot(d, color = '#b02538', edgecolor = 'black', alpha=1, binwidth=1, binrange = [-.5,upper_bound+1.5], stat = 'density', legend = False)
    plt.xlabel("Distance")
    plt.ylabel("Proportion of trees")
    if hspr == 1:
        plt.savefig("SPR/plots/rspr_distribution_" + str(num_leaves) + "_n_" + str(num_tree_pairs) + ".eps")
    else:
        plt.savefig("SPR/plots/hspr_distribution_" + str(num_leaves) + "_n_" + str(num_tree_pairs) + ".eps")
    plt.clf()
    # plt.show()
    # plts.plot_hist(distances, bins, output_file)


# use own implementation of coalescent to plot difference in RSPR/HSPR distances between two coalescent trees and the same trees with one leaf deleted
def distance_del_leaf(num_leaves, num_deletions, num_tree_pairs, hspr = 1, output_file = '', distances_file = ''):
    # Plotting the distances for num_tree_pairs simulated pairs of trees and save plot (if filehandle given) in output_file
    distances = []

    for i in range(0,int(num_tree_pairs)):
        if i%100 == 0:
            print('iteration', i)
        tree_list = sim_coal(num_leaves,2) # Simulate a pair of trees instead of a list with num_tree trees
        d = len(rankedspr_bfs(tree_list.trees[0], tree_list.trees[1]))-1
        # try deleting every leaf and see how distance decreases
        max_dist = d
        for i in range(0,num_leaves):
            tree1 = del_leaf(tree_list.trees[0],i)
            tree2 = del_leaf(tree_list.trees[1],i)
            current_dist = len(rankedspr_bfs(tree1, tree2))-1
            if current_dist<max_dist:
                max_dist = current_dist
        distances.append(d-max_dist)

        # # alternatively: try to delete every pair of leaves and look at minimum distance
        # current_dist = []
        # for i in range(0,num_leaves-1):
        #     tree1 = del_leaf(tree_list.trees[0],i)
        #     tree2 = del_leaf(tree_list.trees[1],i)
        #     for j in range(0,num_leaves-2):
        #         tree1_1 = del_leaf(tree1,j)
        #         tree2_1 = del_leaf(tree2,j)
        #         current_dist.append(len(rankedspr_bfs(tree1_1, tree2_1))-1)
        #     print(d - max(current_dist), i, j, tree_to_cluster_string(tree_list.trees[0]), tree_to_cluster_string(tree_list.trees[1]))
        # distances.append(d - max(current_dist))

        # # even another alternative: delete the two cherry leaves
        # c1 = min(tree1.tree[num_leaves].children[0], tree1.tree[num_leaves].children[1])
        # c2 = max(tree1.tree[num_leaves].children[0], tree1.tree[num_leaves].children[1])
        # tree1 = del_leaf(tree1, c2)
        # tree1 = del_leaf(tree1, c1)
        # tree2 = del_leaf(tree2, c2)
        # tree2 = del_leaf(tree2, c1)
        # d1 = len(rankedspr_bfs(tree1, tree2))-1
        # distances.append(d-d1)

        # if d-d1 == 3:
        #     print("original trees:")
        #     print(tree_to_cluster_string(tree_list.trees[0]))
        #     print(tree_to_cluster_string(tree_list.trees[1]))
        #     print("trees after deleting leaves:")
        #     print(tree_to_cluster_string(tree1))
        #     print(tree_to_cluster_string(tree2))
    print(distances)

    print("maximum differences in distances:", max(distances))
    if distances_file != '':
        np.savetxt(distances_file,  distances, delimiter = ' ')
    # Plot histogram
    d = pd.DataFrame(data=distances)
    upper_bound = max(distances)
    b = np.arange(-.5, upper_bound + 1.5, 1)
    sns.set_theme(font_scale=1.2)
    sns.histplot(d, color = '#b02538', edgecolor = 'black', alpha=1, binwidth=1, binrange = [-.5,upper_bound+1.5], stat = 'density', legend = False)
    plt.xlabel("Distance")
    plt.ylabel("Proportion of trees")
    if hspr == 1:
        plt.savefig("SPR/plots/rspr_dist_diff_" + str(num_leaves) + "_n_" + str(num_tree_pairs) + ".eps")
    else:
        plt.savefig("SPR/plots/hspr_dist_diff_" + str(num_leaves) + "_n_" + str(num_tree_pairs) + ".eps")
    plt.clf()
    # plt.show()
    # plts.plot_hist(distances, bins, output_file)


# use own implementation of coalescent to compare RSPR and HSPR distances between trees drawn from uniform distribution
def compare_hspr_rspr_uniform(num_leaves, num_tree_pairs, distances_file = ''):
    # Plotting the distances for num_tree_pairs simulated pairs of trees and save distances (if file handle provided)
    distances = [] # contains HSPR-RSPR distance for all simulated tree pairs
    for i in range(0,int(num_tree_pairs)):
        if i%100 == 0:
            print('iteration', i)
        tree_list = sim_coal(num_leaves,2) # Simulate a pair of trees instead of a list with num_tree trees
        distances.append(len(rankedspr_bfs(tree_list.trees[0], tree_list.trees[1], hspr=0))-len(rankedspr_bfs(tree_list.trees[0], tree_list.trees[1],hspr=1)))
    if distances_file != '':
        np.savetxt(distances_file,  distances, delimiter = ' ')
    # Plot histogram
    d = pd.DataFrame(data=distances)
    upper_bound = max(distances)
    b = np.arange(-.5, upper_bound + 1.5, 1)
    sns.set_theme(font_scale=1.2)
    sns.histplot(d, color = '#b02538', edgecolor = 'black', alpha=1, binwidth=1, binrange = [-.5,upper_bound+1.5], stat = 'density', legend = False)
    plt.xlabel("Distance")
    plt.ylabel("Proportion of trees")
    plt.savefig("SPR/plots/rspr_hspr_difference_" + str(num_leaves) + "_n_" + str(num_tree_pairs) + ".eps")
    plt.show()
    plt.clf()


# use own implementation of coalescent to compare differences between RSPR and HSPR shortest paths -- might be useful to determine if rank moves are always at beginning or end of shortest paths
def compare_hspr_rspr(num_leaves, num_tree_pairs):
    for i in range(0,int(num_tree_pairs)):
        if i%100 == 0:
            print('iteration', i)
        tree_list = sim_coal(num_leaves,2) # Simulate a pair of trees instead of a list with num_tree trees
        hspr_path = rankedspr_bfs(tree_list.trees[0], tree_list.trees[1], hspr=0)
        rspr_path = rankedspr_bfs(tree_list.trees[0], tree_list.trees[1], hspr=1)
        if(len(hspr_path)!=len(rspr_path)):
            print("hspr distance:", len(hspr_path)-1, "rspr_dist:", len(rspr_path)-1)
            print("hspr path:")
            for tree in hspr_path:
                print(tree)
            print("rspr path:")
            for tree in rspr_path:
                print(tree)


def find_rank_moves(num_leaves, num_tree_pairs):
    # simulate num_tree_pairs pairs of trees on num_leaves leaves and check the position of rank moves on shortest paths between those trees in RSPR (using BFS)
    # prints shortest paths that have rank moves not at the start or beginning, but somewhere in the middle
    for i in range(0,num_tree_pairs):
        tree_pair = sim_coal(num_leaves, 2)
        path = rankedspr_bfs(tree_pair.trees[0], tree_pair.trees[1])
        for i in range(0,len(path)-1):
            tree1_sorted = ''.join(sorted(str(path[i])))
            tree2_sorted = ''.join(sorted(str(path[i+1])))
            if tree1_sorted == tree2_sorted and i != 0 and i != len(path)-2:
                # two trees are connected by a rank move if the cluster strings contain exactly the same characters (are permutations of each other)
                print("rank move between:")
                print(path[i])
                print(path[i+1])
                print("entire path:")
                for tree in path:
                    print(tree)


def caterpillar_diameter_trees(n, hspr=1):
    # Checking which trees have diameter distance from identity caterpillar
    print("Reading trees")
    if hspr ==1:
        file = open('SPR/tree_dict_' + str(n) + '_leaves.txt')
        d = np.load('SPR/distance_matrix_' + str(n) + '_leaves.npy')
    else:
        file = open('SPR/tree_dict_' + str(n) + '_leaves_hspr.txt')
        d = np.load('SPR/distance_matrix_' + str(n) + '_leaves_hspr.npy')
    content = file.readlines()
    print("Done reading trees")

    max_indices = np.where(d == np.amax(d))
    max_coordinates = list(zip(max_indices[0], max_indices[1]))
    print("number of tree pair with diameter distance:")
    print(len(max_coordinates)/2)
    count = 0
    num_max_dist = 0
    # print(len(content[0]), content[0])
    for index1 in max_indices[1]:
        if max_indices[0][count] != 0:
            break
        count += 1
        print(index1, len(content[index1]), content[index1])
        # We only need to compare against first tree in file, as this is identity caterpillar tree (bc of symmetry)
        # if content[index1].count(',') == content[0].count(','): # check if content[index2] is caterpillar tree
        #     # print(content[0], content[index1])
        #     num_max_dist +=1

    print("number of caterpillar trees with diameter distance from identity caterpillar:", num_max_dist)
    print("total number of trees with diameter distance from identity caterpillar:", count)


def orbit_sizes(n, hspr=1):
    # find the number of trees at distance k from any tree in the distance matrix computed by SEIDEL
    # Output is an array of orbit sizes, where unique ones are only given once (e.g. all orbit sizes for same ranked topology will be the same)

    num_trees = int(math.factorial(n) * math.factorial(n-1) / (2**(n-1)))
    print("Start reading distance matrix")
    if hspr == 1:
        d = np.load('SPR/distance_matrix_' + str(n) + '_leaves.npy')
    else:
        d = np.load('SPR/distance_matrix_' + str(n) + '_leaves_hspr.npy')
    print("Done reading distance matrix")
    orbit_size = np.zeros((int(num_trees), int(np.amax(d)+1))) # initialise orbit sizes as zero matrix

    for i in range(0,num_trees):
        for j in range(0,np.amax(d)+1):
            orbit_size[i][j] = np.count_nonzero(d[i]==j)
            # print("distance", i, ":", num_trees, "trees")
    unique_rows = np.unique(orbit_size, axis=0, return_index = True)
    return(unique_rows) # unique_rows[0] contains the unique orbit sizes and unique_rows[1] contains the indices belonging to trees having those orbit sizes.


def print_orbits_with_trees(n, hspr=1):
    orbits = orbit_sizes(n, hspr)
    if hspr == 0:
        f = open('SPR/tree_dict_' + str(n) + '_leaves_hspr.txt')
    else:
        f = open('SPR/tree_dict_' + str(n) + '_leaves.txt')
    trees = f.readlines()
    for i in range(0,len(orbits[0])):
        print(str(trees[orbits[1][i]]), orbits[0][i])
    f.close()


def orbit_count_repetitions(tree, hspr=1):
    # print for every tree in 2-NH of tree how often it is counted if we perform two HSPR/RSPR moves on tree
    one_orbit_dict = dict()
    two_orbit_dict = dict()
    if hspr == 0:
        one_orbit = hspr_neighbourhood(tree)
    else:
        one_orbit = spr_neighbourhood(tree)
    # add all trees in 1-NH to one_orbit_dict
    for i in range(0,one_orbit.num_trees):
        one_orbit_dict[tree_to_cluster_string(one_orbit.trees[i])] = 1
    for i in range(0,one_orbit.num_trees):
        if hspr == 0:
            two_orbit = hspr_neighbourhood(one_orbit.trees[i])
        else:
            two_orbit = spr_neighbourhood(one_orbit.trees[i])
        for j in range(0,two_orbit.num_trees):
            tree_str = tree_to_cluster_string(two_orbit.trees[j])
            if tree_str in one_orbit_dict:
                one_orbit_dict[tree_str] += 1
            elif tree_str in two_orbit_dict:
                two_orbit_dict[tree_str] += 1
            elif tree_str == tree_to_cluster_string(tree): # ignore the initial tree
                pass
            else:
                two_orbit_dict[tree_str] = 1
    print("Size of 2-orbit:", len(two_orbit_dict))
    print("Size of 2-NH:", 1+len(one_orbit_dict)+len(two_orbit_dict))
    return(one_orbit_dict, two_orbit_dict)


# Check how many shortest tree pairs have shortest paths with a caterpillar tree on them (only possible for a small number of leaves!)
def check_caterpillar_on_shortest_path(num_leaves, hspr=1):
    if hspr == 1:
        d = np.load('SPR/distance_matrix_' + str(num_leaves) + '_leaves.npy')
    else:
        d = np.load('SPR/distance_matrix_' + str(num_leaves) + '_leaves_hspr.npy')

    if hspr == 0:
        f = open('SPR/tree_dict_' + str(num_leaves) + '_leaves_hspr.txt', 'r')
    else:
        f = open('SPR/tree_dict_' + str(num_leaves) + '_leaves.txt', 'r')

    num_ctrees_on_paths = 0

    num_trees = len(d)

    c_tree = identity_caterpillar(num_leaves)
    c_indices = [] # list of indices in tree_dict that correspond to caterpillar trees
    count = 0
    for line in f:
        tree_str = line[line.rfind('b')+1:]
        tree_str = tree_str[:tree_str.rfind(' ')]
        if same_topology(read_from_cluster(tree_str), c_tree)==0:
            c_indices.append(count)
        count += 1
    f.close()

    for i in range(0,num_trees):
        if math.floor(i%(num_trees/100)) == 0:
            print("progress:", i/num_trees)
        for j in range(i+1, num_trees):
            flag = False
            for k in c_indices: # check for every tree k if it is on a shortest i-j-path
                if d[i][k] + d[k][j] == d[i][j]:
                    flag = True
                    num_ctrees_on_paths += 1
                    break
                if flag == True:
                    break
            # if flag==False:
            #     print(i, j)
    print(num_ctrees_on_paths, "out of", (num_trees**2-num_trees)/2, "tree pairs have a path that has at least one caterpillar tree in them")
    return(num_ctrees_on_paths, num_trees)


def print_trees_at_diameter(num_leaves, hspr=1):
    (d, tree_dict, tree_index_dict) = read_distance_matrix(num_leaves, hspr)
    d_max = np.amax(d)
    print('diameter:', d_max)
    # print('trees at diameter distance:')
    tree_pairs = [] # actual trees at diameter distance (only one per topology pair)
    count = 0
    for coord in np.argwhere(d == d_max):
        count+=1
        tree1_str = tree_index_dict[coord[0]]
        tree2_str = tree_index_dict[coord[1]]
        tree1 = read_from_cluster(tree1_str)
        tree2 = read_from_cluster(tree2_str)
        # print('tree1:', tree1_str)
        # print('tree2:', tree2_str)
        if len(tree_pairs) == 0:
            tree_pairs.append(set([tree1_str, tree2_str]))
        # print('tree pairs:', tree_pairs)
        topology_already_counted = False
        for i in range(0,len(tree_pairs)):
            tp = tree_pairs[i]
            # print('tp:', tp)
            t1_str = tp.pop()
            t2_str = tp.pop()
            t1 = read_from_cluster(t1_str)
            t2 = read_from_cluster(t2_str)
            tree_pairs[i] = set([t1_str, t2_str])
            if ((same_topology(t1,tree1)+same_topology(t2,tree2)== 0) or (same_topology(t2,tree1)+same_topology(t1,tree2)==0)):
                topology_already_counted = True
                break
        if topology_already_counted == False:
            tree_pairs.append(set([tree1_str, tree2_str]))
    print('tree pairs at diameter distance (only one pair given per topology):')
    for pair in tree_pairs:
        print(pair)
    # print("diameter dist trees per topology:")
    # for topology in all_topologies:
    #     count = 0
    #     for pair in topology_pairs:
    #         if topology in pair:
    #             count +=1
    #     print("number of neighbours for topology", topology, ":", count)

    print("number of tree topology pairs:", len(tree_pairs))


# check if two trees have same unranked topology]
def same_unranked_tree(tree1, tree2):
    cluster_pattern = r'\{[^\}]*\}'
    tree1_str = str(tree_to_cluster_string(tree1))
    clusters1 = re.findall(cluster_pattern, tree1_str)
    tree2_str = str(tree_to_cluster_string(tree2))
    clusters2 = re.findall(cluster_pattern, tree2_str)
    if sorted(clusters1) == sorted(clusters2):
        return(True)
    else:
        return(False)


# Find longest shortest paths with only rank moves on them
def longest_rank_shortest_path(num_leaves):
    (d, tree_dict, tree_index_dict) = read_distance_matrix(num_leaves, hspr = 1)
    current_d = max_dist
    found_path = False # did we find a path with only rank moves on it?
    while(found_path==False):
        print("current distance:", current_d)
        print("number of trees at this distance:", len(np.argwhere(d==current_d)))
        for coord in np.argwhere(d == current_d):
            tree1_str = tree_index_dict[coord[0]]
            tree2_str = tree_index_dict[coord[1]]
            tree1 = read_from_cluster(tree1_str)
            tree2 = read_from_cluster(tree2_str)
            if same_unranked_tree(tree1, tree2):
                # Get length of shortest path that only has rank moves
                num_rank_moves = shortest_rank_path(tree1,tree2)
                if num_rank_moves == current_d:
                    found_path = True
                    print('Maximum length of a rank move only path is:', current_d)
                    print('Given by trees:\n', tree1_str, "\n", tree2_str)
                    return(0)
        current_d -=1


# simulate two trees (coalescent) and see whether there is a tree in 1-NH of starting tree resulting from rank move
def path_rank_moves_first(num_leaves, num_repeats):
    (d, tree_dict, tree_index_dict) = read_distance_matrix(num_leaves, hspr = 1)

    for j in range(0,num_repeats):
        tree_list = sim_coal(num_leaves,2)
        tree1 = tree_list.trees[0]
        tree2 = tree_list.trees[1]
        tree1_str = str(tree_to_cluster_string(tree1)).split("'")[1]
        tree2_str = str(tree_to_cluster_string(tree2)).split("'")[1]

        tree1_index = tree_dict[tree1_str]
        tree2_index = tree_dict[tree2_str]

        rank_neighbours = all_rank_neighbours(tree1)
        for i in range(0,rank_neighbours.num_trees):
            neighbour_str = str(tree_to_cluster_string(rank_neighbours.trees[i])).split("'")[1]
            neighbour_index = tree_dict[neighbour_str]
            if d[tree1_index][neighbour_index] + d[neighbour_index][tree2_index] == d[tree1_index][tree2_index]:
                print("start:", tree1_str)
                print("neighbour:", neighbour_str)
                print("end:", tree2_str)


# Compute the maximum number of rank moves on a shortest path in RSPR (using the distance matrix for the whole tree space computed by SEIDEL)
def max_rank_move_shortest_path(tree1, tree2):
    (d, tree_dict, tree_index_dict) = read_distance_matrix(num_leaves, hspr = 1)

    tree1_str = str(tree_to_cluster_string(tree1)).split("'")[1]
    tree2_str = str(tree_to_cluster_string(tree2)).split("'")[1]

    tree1_index = tree_dict[tree1_str]
    tree2_index = tree_dict[tree2_str]

    distance = d[tree1_index][tree2_index]

    # for every tree that is on a shortest path, save all predecessors of it in dictionary pred:
    pred = dict()
    for tree_index in range(0,len(d)):
        if d[tree1_index][tree_index] + d[tree_index][tree2_index] == distance:
            tree = read_from_cluster(tree_index_dict[tree_index])
            neighbourhood = spr_neighbourhood(tree)
            for i in range(0, neighbourhood.num_trees):
                predecessor = neighbourhood.trees[i]
                pred_str = str(tree_to_cluster_string(predecessor)).split("'")[1]
                pred_index = tree_dict[pred_str]
                if d[tree1_index][pred_index] + d[pred_index][tree_index] + d[tree_index][tree2_index] == distance: # if predecessor is on shortest path from tree1 to tree2
                    if tree_index in pred:
                        pred[tree_index].add(pred_index)
                    else:
                        pred[tree_index] = set([pred_index])

    # print("starting tree:", tree1_str)
    # print("destination tree:", tree2_str)
    # for i in pred:
    #     for j in pred[i]:
    #         print(tree_index_dict[j], tree_index_dict[i])
    # print(len(pred))

    max_rank_moves = 0

    # print("start second part")
    # print(pred)

    # We now need to transform the predecessor dict into actual shortest paths and count how many rank moves are on each of these paths.
    found = False
    while True:
        current_path_rank_moves = 0
        # build path from end to beginning. Delete trees from pred dict, if all pred (i.e. all shortest path containing that tree) are considered.
        last_tree_index = tree2_index
        last_tree = read_from_cluster(tree_index_dict[tree2_index])
        last_popped = -1 # index of the last tree removed from pred[last_pooped_pred]
        last_popped_pred = -1
        while last_tree_index != tree1_index:
            # print(pred[last_tree_index])
            tree_index = pred[last_tree_index].pop()
            # print(tree_index)

            # we only delete the index out of the pred values if it was the last one where there were multiple choices on the currently computed path.
            if len(pred[last_tree_index]) >=1:
                if last_popped != -1:
                    if last_popped_pred in pred:
                        pred[last_popped_pred].add(last_popped)
                    else:
                        pred[last_popped_pred] = set([last_popped])
                last_popped = tree_index
                last_popped_pred = last_tree_index
            else:
                pred[last_tree_index].add(tree_index)
            # if tree_index in pred and len(pred[tree_index])>1: # if there are further paths going through tree_index, we add it back to the predecessor list of last_tree_index
            #     pred[last_tree_index].add(tree_index)
            if len(pred[last_tree_index])==0: # delete empty sets from pred (all paths through corresponding tree have already been considered)
                pred.pop(last_tree_index)
            tree_str = tree_index_dict[tree_index]
            tree = read_from_cluster(tree_str)
            if same_unranked_tree(tree,last_tree):
                current_path_rank_moves += 1
            # else:
            #     print("HSPR move")
            last_tree_index = tree_index
            last_tree = tree
        if current_path_rank_moves > max_rank_moves:
            max_rank_moves = current_path_rank_moves
        # print(current_path_rank_moves)
        if found == True:
            break
        done = True
        for i in pred:
            if len(pred[i]) != 1:
                done = False
        if done == True:
            found = True
    return(max_rank_moves)


# check max number of rank moves on shortest path for all tree pairs in RSPR
def check_max_rank_move_shortest_path(num_leaves):
    (d, tree_dict, tree_index_dict) = read_distance_matrix(num_leaves, hspr = 1)

    max_rank_moves = 0 # maximum number of rank moves among all shortest paths between all pairs of trees
    for i in range(0,len(tree_index_dict)):
        tree1 = read_from_cluster(tree_index_dict[i])
        for j in range(i+1,len(tree_index_dict)):
            tree2 = read_from_cluster(tree_index_dict[j])
            current_rank_moves = max_rank_move_shortest_path(tree1,tree2)
            if max_rank_moves < current_rank_moves:
                max_rank_moves = current_rank_moves
                print(tree_to_cluster_string(tree1), tree_to_cluster_string(tree2))
    return(max_rank_moves)


def test_bottom_up_hspr_approximation(num_leaves, hspr=1):
    (d, tree_dict, tree_index_dict) = read_distance_matrix(num_leaves, hspr)
    
    # Most of the above is not necessary, as there seems to be a problem with dcd tr    

    # print(tree_index_dict)
    differences = [] # array of differences between approximated and actual distances
    for i in range(0,len(d)):
        tree1_str = tree_index_dict[i]
        tree1 = read_from_cluster(tree1_str)
        for j in range(i+1,len(d)):
            tree2_str = tree_index_dict[j]
            tree2 = read_from_cluster(tree2_str)
             # for some reason using the matrix d gives wrong results.
             # there might be something wrong with the computation of d??
            differences.append(rankedspr_path_bottom_up_hspr_dist(tree1,tree2)-d[i][j])
            if (differences[len(differences)-1] != 0):
                print('start tree:', tree1_str)
                print('destination tree:', tree2_str)
                print(d[i][j], rankedspr_path_bottom_up_hspr_dist(tree1,tree2))
                # print("computed path:")
                # path = rankedspr_path_bottom_up_hspr(tree1,tree2)
                # for k in range(0,path.num_trees):
                #     print(tree_to_cluster_string(path.trees[k]))
    print(differences)


def test_rankedspr_path_restricting_neighbourhood(num_leaves, hspr=0):
    (d, tree_dict, tree_index_dict) = read_distance_matrix(num_leaves, hspr)

    differences = []
    for i in range(0,len(d)):
        tree1_str = tree_index_dict[i]
        tree1 = read_from_cluster(tree1_str)
        for j in range(i+1,len(d)):
            tree2_str = tree_index_dict[j]
            tree2 = read_from_cluster(tree2_str)
            approx_dist = rankedspr_path_restricting_neighbourhood(tree1,tree2,hspr)
            actual_dist = d[i][j]
            differences.append(approx_dist - actual_dist)
            # if differences[len(differences)-1] > 0:
            #     print(approx_dist, actual_dist)
            #     print(tree1_str)
            #     print(tree2_str)
    print(max(differences))


# Try to find the longest sequence of RNNI moves at the beginning of a shortest path from tree1 to tree2
def find_longest_rnni_block(tree1, tree2):
    num_leaves = tree1.num_leaves
    (d, tree_dict, tree_index_dict) = read_distance_matrix(num_leaves, hspr = 1)

    tree1_str = str(tree_to_cluster_string(tree1)).split("'")[1]
    tree2_str = str(tree_to_cluster_string(tree2)).split("'")[1]
    tree1_index = tree_dict[tree1_str]
    tree2_index = tree_dict[tree2_str]

    print("start:", tree1_str)
    print("destination:", tree2_str)
    print("hspr distance:", d[tree1_index][tree2_index])

    max_rnni_dist = 0
    max_rnni_tree_str = ''
    for i in range(0,len(d)):
        if d[tree1_index][i] + d[i][tree2_index] == d[tree1_index][tree2_index]:
            tree = read_from_cluster(tree_index_dict[i])
            drnni = findpath_distance(tree1, tree)
            if d[tree1_index][i] == drnni and drnni > max_rnni_dist:
                max_rnni_dist = drnni
                max_rnni_tree_str = tree_index_dict[i]
    print("maximum number of rnni moves at beginning of path:", max_rnni_dist)
    print("last tree in sequence of rnni moves:", max_rnni_tree_str)
    return(max_rnni_dist)


# Try to find the longest sequence of RNNI moves at the beginning of a shortest path from tree1 to tree2
def find_longest_rank_block(tree1, tree2):
    num_leaves = tree1.num_leaves
    (d, tree_dict, tree_index_dict) = read_distance_matrix(num_leaves, hspr = 1)

    tree1_str = str(tree_to_cluster_string(tree1)).split("'")[1]
    tree2_str = str(tree_to_cluster_string(tree2)).split("'")[1]
    tree1_index = tree_dict[tree1_str]
    tree2_index = tree_dict[tree2_str]

    print("start:", tree1_str)
    print("destination:", tree2_str)
    print("hspr distance:", d[tree1_index][tree2_index])

    max_rank_dist = 0
    max_rank_tree_str = ''
    for i in range(0,len(d)):
        if d[tree1_index][i] + d[i][tree2_index] == d[tree1_index][tree2_index]:
            tree = read_from_cluster(tree_index_dict[i])
            drank = findpath_distance(tree1, tree)
            if d[tree1_index][i] == drank and same_unranked_tree(tree, tree1) and drank > max_rank_dist:
                max_rank_dist = drank
                max_rank_tree_str = tree_index_dict[i]
                # print(tree1_str, max_rank_tree_str)
    print("maximum number of rank moves at beginning of path:", max_rank_dist)
    print("last tree in sequence of rank moves:", max_rank_tree_str)
    return(max_rank_dist)


def test_rankedspr_path_rnni_mrca_diff(num_leaves):
    (d, tree_dict, tree_index_dict) = read_distance_matrix(num_leaves, hspr = 1)

    num_tree_pairs=0
    correct_distance = 0
    for i in range(0,len(d)):
        tree1_str = tree_index_dict[i]
        tree1 = read_from_cluster(tree1_str)
        for j in range(i+1,len(d)):
            num_tree_pairs+=1
            tree2_str = tree_index_dict[j]
            tree2 = read_from_cluster(tree2_str)
            print("tree1:", tree1_str)
            print("tree2:", tree2_str)
            approx_rnni_path = rankedspr_path_rnni_mrca_diff(tree1, tree2, 1)

            print("path:")
            for i in range(0,approx_rnni_path.num_trees):
                print(tree_to_cluster_string(approx_rnni_path.trees[i]))

            approx_rnni_dist = approx_rnni_path.num_trees-1
            actual_rnni_dist = find_longest_rnni_block(tree1, tree2)
            print(approx_rnni_dist)
            print(actual_rnni_dist)
            if (approx_rnni_dist == actual_rnni_dist):
                correct_distance += 1
            # else:
    print('correct distance:', correct_distance, 'out of', num_tree_pairs)


def test_rankedspr_path_rank_mrca_diff(num_leaves):
    (d, tree_dict, tree_index_dict) = read_distance_matrix(num_leaves, hspr = 1)

    num_tree_pairs=0
    correct_distance = 0
    for i in range(0,len(d)):
        tree1_str = tree_index_dict[i]
        tree1 = read_from_cluster(tree1_str)
        for j in range(i+1,len(d)):
            num_tree_pairs+=1
            tree2_str = tree_index_dict[j]
            tree2 = read_from_cluster(tree2_str)
            approx_rank_path = rankedspr_path_rnni_mrca_diff(tree1, tree2, 0)

            # print("tree1:", tree1_str)
            # print("tree2:", tree2_str)
            # print("path:")
            # for i in range(0,approx_rank_path.num_trees):
            #     print(tree_to_cluster_string(approx_rank_path.trees[i]))

            approx_rank_dist = approx_rank_path.num_trees-1
            actual_rank_dist = find_longest_rank_block(tree1, tree2)
            # print(approx_rank_dist)
            # print(actual_rank_dist)
            if (approx_rank_dist == actual_rank_dist):
                correct_distance += 1
            else:
                print("approximation:", approx_rank_dist, "actual:", actual_rank_dist)
    print('correct distance:', correct_distance, 'out of', num_tree_pairs)


# compute the sum of sizes of symmetric differences of sets of ancestors for every leaf between tree1 and tree2
def symm_ancestor_diff(tree1, tree2):
    num_leaves = tree1.num_leaves
    symm_diff = 0
    for i in range(0,num_leaves):
        # get ancestors of tree1
        ancestors1 = set([]) # set of ancestors of leaf i
        next_ancestor1 = i
        while next_ancestor1 != 2*num_leaves-2: # iterate until we reach root
            next_ancestor1 = tree1.tree[next_ancestor1].parent
            ancestors1.add(next_ancestor1)
        # get ancestors of tree2
        ancestors2 = set([]) # set of ancestors of leaf i
        next_ancestor2 = i
        while next_ancestor2 != 2*num_leaves-2: # iterate until we reach root
            next_ancestor2 = tree2.tree[next_ancestor2].parent
            ancestors2.add(next_ancestor2)
        symm_diff += len(ancestors1.symmetric_difference(ancestors2))
    return symm_diff


def approx_symm_ancestor_dist(tree1, tree2, hspr=1):
    # test if the idea of minimising the symmetric difference of ancestor sets for all leaves gives shortest paths -- allow to change between hspr&rspr
    num_leaves = tree1.num_leaves
    next_tree = tree1 # don't change input tree
    approx_dist = 0 # approximated distance -- this will be the output
    if hspr >= 0:
        while (same_tree(next_tree,tree2) != 0):
            neighbours = all_spr_neighbourhood(next_tree, hspr)
            min_diff = symm_ancestor_diff(next_tree, tree2) # we aim to minimise this value
            for i in range(0,neighbours.num_trees):
                symm_diff = symm_ancestor_diff(neighbours.trees[i], tree2)
                # print(min_diff, symm_diff)
                if (symm_diff <= min_diff): # strict < doesn't always give a path!
                    min_diff = symm_diff
                    next_tree = neighbours.trees[i]
            # print(tree_to_cluster_string(next_tree))
            approx_dist += 1
    else: # if hspr is negative, we assume that we only want to get the number of rank moves at the beginning of a path that decrease symm_diff
        change = True # indicates if we did a rank move in the last iteration
        while change == True:
            change = False
            neighbours = all_rank_neighbours(next_tree) # change this to rnni_neighbourhood(next_tree) to check the same for RNNI moves -- doesn't give shortest path either!
            min_diff = symm_ancestor_diff(next_tree, tree2) # we aim to minimise this value
            for i in range(0,neighbours.num_trees):
                symm_diff = symm_ancestor_diff(neighbours.trees[i], tree2)
                if (symm_diff < min_diff):
                    min_diff = symm_diff
                    next_tree = neighbours.trees[i]
                    change = True
            if change == True:
                approx_dist += 1
    return approx_dist, next_tree # in case of hspr >= 0, next_tree is tree2


def test_approx_symm_ancestor_dist(num_leaves, hspr=1):
    (d, tree_dict, tree_index_dict) = read_distance_matrix(num_leaves, hspr)

    num_tree_pairs=0
    correct_distance = 0
    for i in range(0,len(d)):
        if ((100*i/len(d))%5==0):
            print("progress:", int(100*i/len(d)), "percent")
        tree1_str = tree_index_dict[i]
        tree1 = read_from_cluster(tree1_str)
        for j in range(i+1,len(d)):
            num_tree_pairs+=1
            tree2_str = tree_index_dict[j]
            tree2 = read_from_cluster(tree2_str)

            # print("tree1:", tree1_str)
            # print("tree2:", tree2_str)
            approx_dist = approx_symm_ancestor_dist(tree1, tree2, hspr)
            if hspr >= 0:
                actual_dist = d[i][j]
                if (approx_dist[0] == actual_dist):
                    correct_distance += 1
                else:
                    if (approx_dist[0] - actual_dist >1):
                        print(tree1_str, tree2_str, actual_dist)
                #     print("approximation:", approx_dist, "actual:", actual_dist)
            else:
                [approx_dist, tree3] = approx_symm_ancestor_dist(tree1, tree2, hspr)
                tree3_str = str(tree_to_cluster_string(tree3)).split("'")[1]
                tree3_index = tree_dict[tree3_str]
                if (approx_dist + d[tree3_index][j] == d[i][j]):
                    correct_distance+=1
                # else:
                #     print(tree1_str, tree3_str, tree2_str)
                #     print(d[i][j], approx_dist, d[tree3_index, j])

    print('correct distance:', correct_distance, 'out of', num_tree_pairs)


# compute the sum of rank differences of all mrcas for every pair of leaves
def pw_mrca_diff(tree1, tree2):
    num_leaves = tree1.num_leaves
    diff = 0
    for i in range(0,num_leaves):
        for j in range(i+1, num_leaves):
            diff += abs(mrca(tree1, i, j)-mrca(tree2, i, j))
    return diff


def approx_pw_mrca_diff_dist(tree1, tree2, hspr=1):
    # test if the idea of minimising the sum of pairwise mrca differences gives us a shortest path
    num_leaves = tree1.num_leaves
    next_tree = tree1 # don't change input tree
    approx_dist = 0 # approximated distance -- this will be the output
    while (same_tree(next_tree,tree2) != 0):
        neighbours = all_spr_neighbourhood(next_tree, hspr)
        min_diff = pw_mrca_diff(next_tree, tree2) # we aim to minimise this value
        for i in range(0,neighbours.num_trees):
            symm_diff = pw_mrca_diff(neighbours.trees[i], tree2)
            # print(min_diff, symm_diff)
            if (symm_diff < min_diff): # strict < doesn't always give a path!
                min_diff = symm_diff
                next_tree = neighbours.trees[i]
        # print(tree_to_cluster_string(next_tree))
        approx_dist += 1
    return approx_dist


# test if approx_symm_ancestor_dist produces distances for all pairs of trees on num_leaves leaves
def test_approx_symm_ancestor_dist(num_leaves, hspr=1):
    (d, tree_dict, tree_index_dict) = read_distance_matrix(num_leaves, hspr)

    num_tree_pairs=0
    correct_distance = 0
    for i in range(0,len(d)):
        if ((100*i/len(d))%5==0):
            print("progress:", int(100*i/len(d)), "percent")
        tree1_str = tree_index_dict[i]
        tree1 = read_from_cluster(tree1_str)
        for j in range(i+1,len(d)):
            num_tree_pairs+=1
            tree2_str = tree_index_dict[j]
            tree2 = read_from_cluster(tree2_str)

            # print("tree1:", tree1_str)
            # print("tree2:", tree2_str)
            approx_dist = approx_pw_mrca_diff_dist(tree1, tree2, hspr)
            actual_dist = d[i][j]
            if (approx_dist == actual_dist):
                correct_distance += 1
            else:
                # if (approx_dist - actual_dist >1):
                print(tree1_str, tree2_str, actual_dist)
                print("approximation:", approx_dist, "actual:", actual_dist)
    print('correct distance:', correct_distance, 'out of', num_tree_pairs)


def min_rnni_spr_neighbour_dist(tree1, tree2, hspr=1):
    # compute a path from tree1 to tree2 iteratively by choosing in every iteration the tree in neighbourhood that has minimum RNNI distance to tree2
    num_leaves = tree1.num_leaves
    next_tree = tree1
    approx_dist = 0
    while (same_tree(next_tree,tree2) != 0):
        neighbours = all_spr_neighbourhood(next_tree, hspr)
        min_diff = findpath_distance(next_tree, tree2)
        for i in range(0,neighbours.num_trees):
            rnni_diff = findpath_distance(neighbours.trees[i], tree2)
            if rnni_diff < min_diff:
                min_diff = rnni_diff
                next_tree = neighbours.trees[i]
        approx_dist += 1
    return approx_dist


# test if min_rnni_spr_neighbour_dist produces distances for all pairs of trees on num_leaves leaves
def test_min_rnni_spr_neighbour_dist(num_leaves, hspr=1):
    (d, tree_dict, tree_index_dict) = read_distance_matrix(num_leaves, hspr)

    false_distance =[]
    num_tree_pairs=0
    correct_distance = 0
    for i in range(0,len(d)):
        tree1_str = tree_index_dict[i]
        tree1 = read_from_cluster(tree1_str)
        for j in range(i+1,len(d)):
            num_tree_pairs+=1
            tree2_str = tree_index_dict[j]
            tree2 = read_from_cluster(tree2_str)
            approx_dist = min_rnni_spr_neighbour_dist(tree1, tree2, hspr)
            actual_dist = d[i][j]
            if (approx_dist == actual_dist):
                correct_distance += 1
            # else:
            #     print(tree1_str, tree2_str, actual_dist)
            #     print("approximation:", approx_dist, "actual:", actual_dist)
            false_distance.append(approx_dist - actual_dist)
    print('correct distance:', correct_distance, 'out of', num_tree_pairs)

    # Plot difference in approximated distances as historgam
    plt.clf()
    d = pd.DataFrame(data=false_distance)
    upper_bound = max(false_distance)
    b = np.arange(-.5, upper_bound + 1.5, 1)
    sns.set_theme(font_scale=1.2)
    sns.histplot(d, palette=['#b02538'], edgecolor = 'black', alpha=1, binwidth=1, binrange = [-.5,upper_bound+1.5], stat = 'density', legend = False)
    plt.xlabel("Difference between approximation and actual distance")
    plt.ylabel("Number of tree pairs")
    plt.savefig("SPR/plots/rnni_to_approx_spr_" + str(num_leaves) + "_n.eps")
    # plt.show()


# Compute the maximum number of rank moves on a shortest path in RSPR (using the distance matrix for the whole tree space computed by SEIDEL)
def count_rank_moves_all_shortest_paths(tree1, tree2, d, tree_dict, tree_index_dict):
    tree1_str = str(tree_to_cluster_string(tree1)).split("'")[1]
    tree2_str = str(tree_to_cluster_string(tree2)).split("'")[1]

    tree1_index = tree_dict[tree1_str]
    tree2_index = tree_dict[tree2_str]

    distance = d[tree1_index][tree2_index]

    # for every tree that is on a shortest path, save all predecessors of it in dictionary pred:
    pred = dict()
    for tree_index in range(0,len(d)):
        if d[tree1_index][tree_index] + d[tree_index][tree2_index] == distance:
            tree = read_from_cluster(tree_index_dict[tree_index])
            neighbourhood = spr_neighbourhood(tree)
            for i in range(0, neighbourhood.num_trees):
                predecessor = neighbourhood.trees[i]
                pred_str = str(tree_to_cluster_string(predecessor)).split("'")[1]
                pred_index = tree_dict[pred_str]
                if d[tree1_index][pred_index] + d[pred_index][tree_index] + d[tree_index][tree2_index] == distance: # if predecessor is on shortest path from tree1 to tree2
                    if tree_index in pred:
                        pred[tree_index].add(pred_index)
                    else:
                        pred[tree_index] = set([pred_index])

    # We now need to transform the predecessor dict into actual shortest paths and count how many rank moves are on each of these paths.
    num_rank_moves = dict() # index: currrent_tree, value: number of rank moves between tree2 and current_tree

    num_rank_moves[tree2_index] = [0]
    next_trees = [tree2_index] # queue with next trees to be current_tree_index (going from big to small distance to tree1)
    while len(next_trees) > 0:
        current_tree_index = next_trees.pop(0)
        current_tree = read_from_cluster(tree_index_dict[current_tree_index])
        while current_tree_index in pred and len(pred[current_tree_index]) > 0:
            # in every loop update the number of rank moves from tree with index i to tree2_index, by adding all shortest path from current_tree to tree2 and add 1 if there is a rank move between tree_i and current_tree
            i = pred[current_tree_index].pop()
            if i != tree1_index and i not in next_trees: # no need to try and find predecessors of tree1 in any future iteration
                next_trees.append(i)
            tree_i = read_from_cluster(tree_index_dict[i])
            if i not in num_rank_moves: # create a list with number of rank moves on all shortest paths from tree_i to tree2, if it doesn't exist already
                num_rank_moves[i] = []
            if same_unranked_tree(tree_i, current_tree):
                num_rank_moves[i] = num_rank_moves[i] + [x+1 for x in num_rank_moves[current_tree_index]] # number of rank moves for all paths to tree_i should be same as to current_tree_index+1 if they are connected by rank move
            else: # no rank moves added between tree_i and current_tree
                num_rank_moves[i] = num_rank_moves[i] + num_rank_moves[current_tree_index]
        pred.pop(current_tree_index) # we are done with current_tree

    return(num_rank_moves[tree1_index])


def rank_moves_distribution(num_leaves):
    (d, tree_dict, tree_index_dict) = read_distance_matrix(num_leaves, hspr = 1)
    max_dist = np.amax(d)
    rank_move_dict = dict() #keys: distances between trees, values: lists of numbers of rank moves on every shortest path between every pair of trees with corresponding distance
    # initialise rank_move_dict:
    for i in range(1,max_dist+1):
        rank_move_dict["dist" + str(i)] = [0] * max_dist

    # for every pair of trees, add list with number of rank moves on shortest paths to rank_move_dict[d] where d is the distance between them
    for i in range(0,len(d)):
        if i%(math.floor(len(d)/100)) == 0:
            print("progress:", int(100*i/len(d)), "percent")
        tree1_str = tree_index_dict[i]
        tree1 = read_from_cluster(tree1_str)
        for j in range(i+1,len(d)):
            tree2_str = tree_index_dict[j]
            tree2 = read_from_cluster(tree2_str)
            rm = count_rank_moves_all_shortest_paths(tree1, tree2, d, tree_dict, tree_index_dict) # list of number of rank moves on all shortest paths between tree1 and tree2
            for k in range(0,max(rm)+1):
                rank_move_dict["dist" + str(d[i][j])][k] += rm.count(k)

    plt.clf()
    # Plot number of rank moves per shortest paths, one line for each possible distance
    d = pd.DataFrame(data=rank_move_dict)
    print(d)
    sns.set_theme(font_scale=1.2)
    sns.lineplot(data = d, markers = True)
    plt.xlabel("Number of rank moves on shortest path")
    plt.ylabel("Number of paths")
    plt.savefig("SPR/plots/rank_move_distribution_" + str(num_leaves) + "_n.eps")
    # plt.clf()
    # plt.show()

    # also plot the 'normalised' number of rank moves on shortest path, i.e. divide the number of paths with x rank moves by the total number of paths:
    norm = dict()
    for i in rank_move_dict:
        norm[i] = [float(x/sum(rank_move_dict[i])) for x in rank_move_dict[i]]
    print(norm)

    # Plot relative number of rank moves per shortest paths, one line for each possible distance
    plt.clf()
    norm_d = pd.DataFrame(data=norm)
    print(norm_d)
    sns.set_theme(font_scale=1.2)
    sns.boxplot(data = norm_d)
    sns.stripplot(data = norm_d, size = 4)
    plt.xlabel("Length of shortest paths")
    plt.ylabel("Relative number of rank moves")
    plt.savefig("SPR/plots/rank_move_distribution_norm_" + str(num_leaves) + "_n_boxplot.eps")
    # plt.show()

    # also do a lineplot for normalised number of rank moves on paths
    plt.clf()
    d = pd.DataFrame(data=norm)
    sns.set_theme(font_scale=1.2)
    sns.lineplot(data = d, markers = True)
    plt.xlabel("Normalised number of rank moves on shortest path")
    plt.ylabel("Number of paths")
    plt.savefig("SPR/plots/rank_move_distribution_norm_" + str(num_leaves) + "_n.eps")


def generate_binary_strings(n):
    # generate list of all binary trings on n leaves (recursively)
    binary_strings = []
    def genbin(n, string=''):
        if len(string) == n:
            binary_strings.append(string)
        else:
            genbin(n, string + '0')
            genbin(n, string + '1')
    genbin(n)
    return binary_strings


def is_embedded(forest, tree):
    # checks if forest is embedded in tree (i.e. forest could be agreement forest for tree) and returns number of connected components
    # The running time of this is VERY low, this function is only used for test on trees on a small number of leaves!
    n = tree.num_leaves
    m = 2*n-1
    conn_comp = dict() # save for every leaf i all other leaves j in same connected component
    for i in range(0,m):
        conn_comp[i] = set([i])

    # Check if for every pair of trees the mrca in forest is either -1 or the same as in tree.
    # If this is the case, all subtrees of forest are subtrees in tree (but: potentially overlapping. we take care of this later)
    # At the same time, we fill the dictionary conn_comp
    for i in range(0,n):
        for j in range(i+1,n):
            if mrca(forest, i, j) == mrca(tree, i, j):
                conn_comp[i].add(j)
                conn_comp[j].add(i)
                # additionally, add all leaves on path from i to mrca to connected component:
                p_i = tree.tree[i].parent
                conn_comp[i].add(p_i)
                conn_comp[j].add(p_i)
                while (p_i != mrca(tree,i,j)):
                    p_i = tree.tree[p_i].parent
                    conn_comp[i].add(p_i)
                    conn_comp[j].add(p_i)
                # the same for j:
                p_j = tree.tree[j].parent
                conn_comp[j].add(p_j)
                conn_comp[i].add(p_j)
                while (p_j != mrca(tree,i,j)):
                    p_j = tree.tree[p_j].parent
                    conn_comp[j].add(p_j)
                    conn_comp[i].add(p_i)
            elif mrca(forest, i, j) != -1:
                return False
    num_components = 0
    leaves_covered = [] # list of leaves for which we already have connected component. This is to count the number of connected components
    for i in range(0,n):
        for j in range(i+1,n):
            intersect = conn_comp[i].intersection(conn_comp[j])
            if len(intersect) > 0 and list(intersect).pop() not in leaves_covered:
                leaves_covered = leaves_covered + list(intersect)
                num_components += 1
            if len(intersect) not in [0,len(conn_comp[i])]:
                return False
    # So far we only counted clusters of size > 1 as connected components. We now need to add count for singletons:
    for i in range(0,n):
        if i not in leaves_covered:
            num_components += 1
    return num_components


def deep_copy(tree):
    n = tree.num_leaves

    # Create a tree in the C data structure
    num_nodes = 2*n-1
    node_list = (NODE * num_nodes)()

    # Initialise Node list
    for i in range(0, num_nodes):
        node_list[i].parent = tree.tree[i].parent
        node_list[i].children[0] = tree.tree[i].children[0]
        node_list[i].children[1] = tree.tree[i].children[1]
        node_list[i].time = tree.tree[i].time

    output = TREE(node_list, n, node_list[num_nodes-1].time,0)
    return(output)


def maf(tree1, tree2):
    # compute a maximum agreement forest for tree1, using exhaustive search (trying out all forests embedded in tree1) -- this is VERY inefficient, but we cannot go past 7 leaves for distance computation anyway, so we accept this for our tests

    if same_tree(tree1, tree2) == 0:
        return(tree1, 1)

    n = tree1.num_leaves
    m = 2*n-1 # number of nodes in node_list
    binary_strings = generate_binary_strings(m-1) # no 0/1 needed for root, bc we always del edge to parent

    # Initialise current_maf as consisting of n singletons
    m = 2*n-1
    node_list = (NODE * m)()
    for i in range(0, m):
        node_list[i].parent = -1
        node_list[i].children[0] = -1
        node_list[i].children[1] = -1
        node_list[i].time = 0
    maf = TREE(node_list, n, node_list[m-1].time,0)
    maf_size = n

    for i in range(0,len(binary_strings)):
        current_maf = deep_copy(tree1) # deep copy tree1
        # only consider constructing AF if it has less trees than already found AF
        for j in range(0,m-1):
            if binary_strings[i][j] == '1':
                # delete edge between node at position j in node_list and its parent
                p = current_maf.tree[j].parent
                current_maf.tree[p].children[0] = -1
                current_maf.tree[p].children[1] = -1
                current_maf.tree[j].parent = -1
        # print('MAF:')
        # for j in range(0,m):
        #     print(j,current_maf.tree[j].parent, current_maf.tree[j].children[0], current_maf.tree[j].children[1])
        # print('end MAF')
        current_maf_size = is_embedded(current_maf, tree2)
        if current_maf_size != False and current_maf_size < maf_size:
            #update maf if it is smaller than previously found af and it is actually an agrrement forest for tree1 and tree2
            maf = deep_copy(current_maf)
            maf_size = current_maf_size

    # print('MAF:')
    # for j in range(0,m):
    #     print(j, maf.tree[j].parent, maf.tree[j].children[0], maf.tree[j].children[1])
    return(maf, maf_size)


def test_mafs_caterpillar(n, num_repeats):
    # test if MAF(T,R)-1 = d(T,R) if T is identity caterpillar tree on n leaves and R random caterpillar tree (num_repeats repitition of the experiment)
    (d, tree_dict, tree_index_dict) = read_distance_matrix(n, hspr = 0)
    tree1 = identity_caterpillar(n)
    tree1_str = str(tree_to_cluster_string(tree1)).split("'")[1]
    tree1_index = tree_dict[tree1_str]
    for i in range(0,num_repeats):
        tree2 = sim_cat(n,1).trees[0]
        tree2_str = str(tree_to_cluster_string(tree2)).split("'")[1]
        tree2_index = tree_dict[tree2_str]
        MAF = maf(tree1, tree2)
        dist = d[tree1_index][tree2_index]
        if MAF[1]-1 != dist:
            print("MAF doesn't give distance for trees:")
            print(tree1_str)
            print(tree2_str)
            print('MAF size:', MAF[1])
            print('MAF:')
            for j in range(0,2*n-1):
                print(j, MAF[0].tree[j].parent, MAF[0].tree[j].children[0], MAF[0].tree[j].children[1])


def test_mafs(n, hspr=0):
    # check for how many trees on n leaves MAF(T,R)-1 != d(T,R)
    (d, tree_dict, tree_index_dict) = read_distance_matrix(n, hspr)
    d_maf_diff = [] # save difference MAF(T,R)-d(T,R) to plot it later
    num_pairs = 0 # total number of pairs we consider
    for i in range(0,len(d)):
        tree1_str = tree_index_dict[i]
        tree1 = read_from_cluster(tree1_str)
        for j in range(i+1,len(d)):
            num_pairs+=1
            tree2_str = tree_index_dict[j]
            tree2 = read_from_cluster(tree2_str)
            MAF = maf(tree1, tree2)
            dist = d[i][j]
            d_maf_diff.append(dist - (MAF[1]-1))
    print("MAF greater than distance for", num_pairs - d_maf_diff.count(0), "out of", num_pairs, "tree pairs")
    # Plot difference MAF(T,R)-d(T,R) in histogram
    plt.clf()
    diff = pd.DataFrame(data=d_maf_diff)
    upper_bound = max(d_maf_diff)
    b = np.arange(-.5, upper_bound + 1.5, 1)
    sns.set_theme(font_scale=1.2)
    sns.histplot(diff, palette=['#b02538'], edgecolor = 'black', alpha=1, binwidth=1, binrange = [-.5,upper_bound+1.5], stat = 'density', legend = False)
    plt.xlabel("|MAF(T,R)|-1-d(T,R)")
    plt.ylabel("Number of tree pairs")
    plt.savefig("SPR/plots/maf_dist_diff_" + str(n) + "_n.eps")


# Use BFS to compute the maximum distance any tree has from start_tree -- save all distances in file
def max_dist_from_tree(start_tree, hspr=1):
    tree_dict = dict() # save trees (as cluster strings) and an index for each tree as value, so we can recover the path after running BFS (backtracking)
    index_dict = dict() # reverse of tree_dict (indices as keys and trees as values)
    predecessor = []
    to_visit = [] # queue containing next trees to be visited in BFS

    # Initialise path?
    current_tree = start_tree

    tree_dict[tree_to_cluster_string(start_tree)] = 0
    index_dict[0] = tree_to_cluster_string(start_tree)
    index = 1 # index of the tree we currently consider (to be put as value for that tree into tree_dict)
    to_visit.append(current_tree)
    # Start BFS
    while len(to_visit) > 0:
        current_tree = to_visit.pop(0)
        current_tree_str = tree_to_cluster_string(current_tree)
        neighbours = all_spr_neighbourhood(current_tree,hspr)
        for i in range(0,neighbours.num_trees):
            tree = neighbours.trees[i]
            neighbour_string = tree_to_cluster_string(tree)
            if neighbour_string not in tree_dict:
                to_visit.append(tree)
                tree_dict[neighbour_string] = index
                index_dict[index]=neighbour_string
                predecessor.append(tree_dict[current_tree_str])
                index+=1
    print('number of trees visited:', len(tree_dict))
    f = open("SPR/distance_single_source/tree_" + str(tree_to_cluster_string(start_tree)).split("'")[1] + ".txt", 'w')
    # backtracking to find actual distances
    diameter = 0
    for dest_tree_str in tree_dict:
        current_index = tree_dict[dest_tree_str]
        path_indices = [current_index]
        while (predecessor[current_index-1] != 0):
            path_indices.append(predecessor[current_index-1])
            current_index = predecessor[current_index-1]
        path_indices.append(0)
        f.write(str(dest_tree_str).split("'")[1] + "\t" + str(len(path_indices)-1) + "\n")
        # now turn path_indices array into path:
        if len(path_indices)-1 > diameter:
            diameter = len(path_indices)-1
    f.close()
    return diameter
