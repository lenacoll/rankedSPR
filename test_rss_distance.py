__author__ = 'Lena Collienne'
# test RSS distance

import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

from rss_distance_functions import *
from treeOclock.tree_parser.tree_io import *
from rankedSPR_seidel import get_distance_matrix



def compare_to_rspr(num_leaves, hspr):
    spr = "rspr"
    if hspr == True:
        spr = "hspr"
    d, tree_dict, tree_index_dict = get_distance_matrix(num_leaves, hspr = hspr)
    num_trees = len(tree_dict)
    distances = []
    for i in range(0, num_trees):
        treei = read_from_cluster(tree_index_dict[i])
        for j in range(i, num_trees):
            treej = read_from_cluster(tree_index_dict[j])
            rss = rss_distance(treei, treej)
            distances.append([d[i][j], rss])
            if rss / d[i][j] > 2:
                print("RSS twice as much as HSPR dist for trees:")
                print(tree_index_dict[i])
                print(tree_index_dict[j])

    df = pd.DataFrame(data = distances, columns = ["HSPR", "RSS"])
    df['frequency'] = df.groupby(['HSPR', 'RSS'])['HSPR'].transform('count')
    sns.scatterplot(data = df, x = "HSPR", y = "RSS", size = "frequency", legend = False)
    # Add KDE plot
    # sns.regplot(data = df, x = 'HSPR', y = 'RSS')
    # Add frequency labels to the points
    for i, row in df.iterrows():
        offset_x = - 0.1  # Adjust the x-coordinate offset
        offset_y = 0.1  # Adjust the y-coordinate offset
        plt.text(row['HSPR'] + offset_x, row['RSS'] + offset_y, row['frequency'], ha='center', va='center')

    # x = range(0, num_leaves)
    # y = [i*2 for i in x]
    # plt.plot(x, y, color='red', linestyle='--')
    plt.plot([df['HSPR'].min(), df['HSPR'].max()], [df['HSPR'].min() * 2, df['HSPR'].max() * 2], 'r--')
    plt.text(df['HSPR'].max() - .2, df['HSPR'].max() * 2 - .2, "f(x)=2x", ha='right', va='bottom', color = "red")
    
    plt.plot([df['HSPR'].min(), df['HSPR'].max()], [df['HSPR'].min(), df['HSPR'].max()], 'g--')
    plt.text(df['HSPR'].max() - .2, df['HSPR'].max(), "f(x)=x", ha='right', va='bottom', color = "green")

    plt.savefig("plots/comparing_rss_hspr_" + str(num_leaves) + "_leaves_" + spr + ".pdf")


def rss_test():
    tree1_str = "[{4,5}:1,{1,2}:2,{1,2,3}:3,{1,2,3,4,5}:4]"
    tree2_str = "[{1,2}:1,{4,5}:2,{1,2,3}:3,{1,2,3,4,5}:4]"

    tree1 = read_from_cluster(tree1_str)
    tree2 = read_from_cluster(tree2_str)

    print(rss_distance(tree1, tree2))


def main():
    compare_to_rspr(5, False)
    


if __name__ == "__main__":
    main()
