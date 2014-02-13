"""Visualize the scatter plot of x, y
"""

import sys
import csv

import matplotlib.pyplot as plot

x, y = [], []
with open(sys.argv[1], 'r') as stream:
    reader = csv.reader(stream, delimiter='\t')
    for row in reader:
        x.append(float(row[0]))
        y.append(float(row[1]))

scatter = plot.scatter(x, y)
plot.setp(scatter, color='r', linewidth=0.0, alpha=0.05)
plot.savefig(sys.argv[2])
