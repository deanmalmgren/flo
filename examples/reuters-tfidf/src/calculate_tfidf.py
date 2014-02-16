"""Calculate the tfidf for every token,document pair in the corpus
"""

import sys
import csv
import collections

df = collections.Counter()
tf = {}

with open(sys.argv[1], 'r') as stream:
    reader = csv.reader(stream)
    for document_id, text in reader:
        grams = text.split()
        df.update(set(grams))
        tf[document_id] = collections.Counter(grams)

writer = csv.writer(sys.stdout)
for document_id, ts in tf.iteritems():
    for gram, t in ts.iteritems():
        d = df[gram]
        writer.writerow([document_id, gram, float(t) / d])
