"""module of general purpose utilities for reading in the data from disk
"""
import csv

def _init_data(cols):
    return [[] for col in cols]    

def data_from_tsv(tsv_filename, cols=None):
    """Load data from tab separated values file located in columns
    specified in cols
    """

    if cols is not None:
        data = _init_data(cols)

    with open(tsv_filename, 'r') as stream:
        reader = csv.reader(stream, delimiter='\t')
        for row in reader:

            if cols is None:
                cols = range(len(row))
                data = _init_data(cols)

            for i, col in enumerate(cols):
                data[i].append(float(row[col]))
    return data
