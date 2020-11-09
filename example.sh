#!/usr/bin/bash

# generate a list of random trees from the fitted primitives in example.fit
# By default it creates two files: expressions.txt and list_primitives.txt
# (names can be changed).
python random_tree.py example.fit


# pick the first tree in the list: expressions.txt
head -n 1 expressions.txt > first_tree.txt


# generate a picture (in file first_tree.png) of the graph using graphviz:
python tree_from_expression.py first_tree.txt list_primitives.txt first_tree.png


# generate a c++ source file corresponding to the random tree:
python create_eval_source.py example.fit first_tree.txt first_tree.cpp


# clean temp files
rm -f expressions.txt
rm -f first_tree.txt
rm -f list_primitives.txt
