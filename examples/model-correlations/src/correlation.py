"""Visualize the scatter plot of x, y
"""

import sys
import math

# use headless matplotlib
# http://stackoverflow.com/a/3054314/564709
import matplotlib
matplotlib.use('Agg')

import matplotlib.pyplot as plot

import loaders

tsv_filename = sys.argv[1]

x, y = loaders.data_from_tsv(tsv_filename)

# # print out the scatter plot. writing PNGs does not do very well for
# # functional tests, so we'll comment it out for now.
# scatter = plot.scatter(x, y)
# plot.setp(scatter, color='r', linewidth=0.0, alpha=0.05)
# plot.savefig(sys.argv[2])

# calculate the correlation
xave = sum(x) / len(x)
yave = sum(y) / len(y)
xsig = math.sqrt(sum((i - xave)*(i - xave) for i in x) / (len(x) - 1))
ysig = math.sqrt(sum((i - yave)*(i - yave) for i in y) / (len(y) - 1))
r = 0.0
for i, j in zip(x, y):
    r += (i - xave)/xsig * (j - yave)/ysig
r /= len(x) - 1
print(r)
