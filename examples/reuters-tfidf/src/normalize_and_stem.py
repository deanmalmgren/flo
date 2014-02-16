"""normalize and stem a document corpus
"""

import sys
import csv
import re

from textblob.nltk.tokenize import RegexpTokenizer
from textblob.nltk.stem import PorterStemmer

tokenizer = RegexpTokenizer(r'\b[a-zA-Z]+\b')
stemmer = PorterStemmer()

writer = csv.writer(sys.stdout)
with open(sys.argv[1], 'r') as stream:
    reader = csv.reader(stream)
    for document_id, text in reader:
        words = []
        for token in tokenizer.tokenize(text):
            words.append(stemmer.stem(token.lower()))
        writer.writerow([document_id, ' '.join(words)])
