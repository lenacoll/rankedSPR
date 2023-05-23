// Computing RSS distance

#include "rss_distance.h"

int rss_distance(Tree* tree1, Tree* tree2){
    long num_leaves = tree1->num_leaves;
    long rss_distance = 0;
    for (long i = 0; i < 2 * num_leaves - 2; i++){
        if(tree1->node_array[i].parent != tree2->node_array[i].parent){
            rss_distance ++;
        }
    }
    return(rss_distance);
}
