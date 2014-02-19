"""Visualize the distribution of values
"""

import sys
import csv

import matplotlib.pyplot as plot

import loaders

tsv_filename = sys.argv[1]
col = int(sys.argv[2])

data = loaders.data_from_tsv(tsv_filename, [col])[0]

scatter = plot.hist(data, 30, normed=1, facecolor='g', alpha=0.6)
plot.savefig(sys.argv[3])
