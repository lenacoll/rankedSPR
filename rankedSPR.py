__author__ = 'Lena Collienne'
# Computing the rankedSPR graph to test algorithms for computing distances for trees on a small number of leaves
import sys
sys.path.append('treeOclock/')
sys.path.append('treeOclock/dct_parser/')

import ctypes
import math
import numpy as np
import random
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


def test_restricted_neighbourhood_search(num_leaves, num_tree_pairs):
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
        # print(tree_to_cluster_string(t_list.trees[i]))
        # print(tree_to_cluster_string(t_list.trees[i+1]))
        # print(rspr_distances[tree1_index][tree2_index], rankedspr_path_restricting_neighbourhood(t_list.trees[i],t_list.trees[i+1]))
        if (rspr_distances[tree1_index][tree2_index] == rankedspr_path_restricting_neighbourhood(t_list.trees[i],t_list.trees[i+1])):
            correct_distance += 1
        else:
            print("tree1:", tree_to_cluster_string(t_list.trees[i]))
            print("tree2:", tree_to_cluster_string(t_list.trees[i+1]))
            print("correct distance:", rspr_distances[tree1_index][tree2_index], "approximated distance:", rankedspr_path_restricting_neighbourhood(t_list.trees[i],t_list.trees[i+1]))
    print('correct distance:', correct_distance, 'out of', num_tree_pairs)


# Very slow and inefficient implementation of BFS for rankedSPR -- only useful for VERY small number of leaves
def rankedspr_bfs(start_tree, dest_tree):
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
        neighbours = spr_neighbourhood(current_tree)
        for i in range(0,neighbours.num_trees):
            tree = neighbours.trees[i]
            neighbour_string = tree_to_cluster_string(tree)
            if neighbour_string not in tree_dict:
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

# test_restricted_neighbourhood_search(5,10000)

# print(sum(rankedSPR_adjacency(4, hspr=0)[0]))
# print(sum(rankedSPR_adjacency(4)[0]))


# t1 = "(((1:1,2:1):2,(3:2,4:2):1):1,5:4);"
# t2 = "((((3:1,5:1):1,2:2):1,1:3):1,4:4);"

# tree1 = read_newick(t1, factor = 0)
# tree2 = read_newick(t2, factor = 0)

# for tree in rankedspr_bfs(tree1, tree2):
#     print(tree)

# print("rankedSPR neighbours:")
# spr_neighbours = spr_neighbourhood(tree1)
# for i in range(0,spr_neighbours.num_trees):
#     print(tree_to_cluster_string(spr_neighbours.trees[i]))


# adj = np.load("SPR/adj_matrix_5_leaves.npy")
# tree1_1nh = set()
# tree2_2nh = set()
# print("adjacency tree1:")
# for i in range(0,180):
#     if(adj[7][i] == 1):
#         print(i)
#         tree1_1nh.add(i)
# print("adjacency tree2:")
# for i in range(0,180):
#     if(adj[154][i] == 1):
#         for j in range(0,180):
#             if(adj[i][j]==1):
#                 tree2_2nh.add(j)
# print(tree1_1nh)
# print(tree2_2nh)
# print(tree1_1nh.intersection(tree2_2nh))
# print(adj[7])
# print(adj[154])
# print(adj.size)
# print(sum(sum(adj)))