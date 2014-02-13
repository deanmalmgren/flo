"""Visualize the distribution of values
"""

import sys
import csv

import matplotlib.pyplot as plot

col = int(sys.argv[2])

data = []
with open(sys.argv[1], 'r') as stream:
    reader = csv.reader(stream, delimiter='\t')
    for row in reader:
        data.append(float(row[col]))

scatter = plot.hist(data, 30, normed=1, facecolor='g', alpha=0.6)
plot.savefig(sys.argv[3])
