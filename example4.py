#import code; code.interact(local=dict(globals(), **locals()))

#!/usr/bin/env python
'''
Linguistic case study

Usage: ./example1.py
'''

# Following the conventions used by scikit-learn
# https://scikit-learn.org/stable/developers/develop.html

from g4l import SmallestMaximizerCriterion
from g4l.estimators.ctm import CTM
from g4l.estimators.prune import Prune
#from g4l.estimators.ctm_scanner import CTMScanner
import g4l.tree.generation as gen
import g4l.tree as tree
from g4l.data import Sample
import logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        #logging.FileHandler("examples/example1/debug.log"),
        logging.StreamHandler()
    ]
)

# Create a sample object instance
X = Sample('examples/example1/folha.txt', [0, 1, 2, 3, 4])
initial_tree = tree.ContextTree(X, max_depth=4, tree_initialization_method=gen.incremental)
tree_a = CTM(initial_tree).execute(1.536489)

# Tree A:   c = 1.536489   (11 contexts)
# tree_a = "000 1 10 100 2 20 200 3 30 300 4"

#pruned_trees = Prune(initial_tree).execute()

#import code; code.interact(local=dict(globals(), **locals()))
