"""Plot the autocorrelation of the specified column
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

scatter = plot.acorr(data, linewidth=3, normed=True)
plot.savefig(sys.argv[3])
