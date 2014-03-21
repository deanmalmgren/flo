"""Run a dummy simulation that outputs tab-separated values
"""

import random
import csv
import sys

writer = csv.writer(sys.stdout, delimiter='\t')
for i in range(10000):
    writer.writerow([
        i,
        i*i,
        i+i,
    ])
