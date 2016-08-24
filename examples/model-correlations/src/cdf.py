"""Visualize the distribution of values
"""

import sys
import csv

# use headless matplotlib
# http://stackoverflow.com/a/3054314/564709
import matplotlib
matplotlib.use('Agg')

import loaders

tsv_filename = sys.argv[1]
col = int(sys.argv[2])

data = loaders.data_from_tsv(tsv_filename, [col])[0]

# # print out the histogram. writing PNGs does not do very well for
# # functional tests, so we'll comment it out for now.
# scatter = plot.hist(data, 30, normed=1, facecolor='g', alpha=0.6)
# plot.savefig(sys.argv[3])

# print out the cumulative distribution function
data.sort()
for i, x in enumerate(data):
    cdf = float(i)/len(data)
    print(x, "%0.4f" % cdf)
