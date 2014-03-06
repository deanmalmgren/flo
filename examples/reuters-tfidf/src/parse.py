"""This script processes the raw SGML and extracts the relevant bits
(in this case text) from the Reuters data set and throws it into a
more managable CSV format for further processing
"""

import sys
import sgmllib
import glob
import os
import csv
from pprint import pprint

class Parser(sgmllib.SGMLParser):
    def __init__(self, writer):
        sgmllib.SGMLParser.__init__(self)
        self.writer = writer
        self.document_id = None
        self.in_body = False
        self.text = ''

    def start_reuters(self, attrs):
        attrs = dict(attrs)
        self.document_id = attrs['newid']

    def end_reuters(self):
        self.writer.writerow([self.document_id, self.text.strip()])
        self.document_id = None
        self.text = ''

    def start_body(self, attrs):
        self.in_body = True

    def end_body(self):
        self.in_body = False

    def handle_data(self, data):
        if self.in_body:
            self.text += ' ' + ' '.join(data.split())

# XXXX BAD DESIGN PATTERN SPECIFYING FILENAMES HERE!!!!
writer = csv.writer(sys.stdout)
for filename in glob.glob(os.path.join(sys.argv[1], "*.sgm")):
    print >> sys.stderr, 'processing %s...' % filename,
    with open(filename, 'r') as stream:
        parser = Parser(writer)
        parser.feed(stream.read())
        sys.stdout.flush()
    print >> sys.stderr, 'done!'
