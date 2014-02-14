"""Visualize the scatter plot of x, y
"""

import sys
import csv

import matplotlib.pyplot as plot

import loaders

tsv_filename = sys.argv[1]

x, y = loaders.data_from_tsv(tsv_filename)

scatter = plot.scatter(x, y)
plot.setp(scatter, color='r', linewidth=0.0, alpha=0.05)
plot.savefig(sys.argv[2])
