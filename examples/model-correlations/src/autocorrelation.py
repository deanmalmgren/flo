"""Plot the autocorrelation of the specified column
"""

import sys
import csv

# use headless matplotlib
# http://stackoverflow.com/a/3054314/564709
import matplotlib
matplotlib.use('Agg')

import matplotlib.pyplot as plot

import loaders

tsv_filename = sys.argv[1]
col = int(sys.argv[2])

data = loaders.data_from_tsv(tsv_filename, [col])[0]

scatter = plot.acorr(data, linewidth=3, normed=True)
plot.savefig(sys.argv[3])
