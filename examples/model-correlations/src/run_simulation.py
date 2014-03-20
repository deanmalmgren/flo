"""Run a dummy simulation that outputs tab-separated values
"""

import random
import csv
import sys

random.seed(int(sys.argv[1]))

writer = csv.writer(sys.stdout, delimiter='\t')
for i in range(10000):
    writer.writerow([
        random.random(),
        random.expovariate(2.0),
        random.normalvariate(10, 15),
    ])
