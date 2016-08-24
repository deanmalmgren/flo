import sys
import csv

from bs4 import BeautifulSoup

# read in html data
with open(sys.argv[1]) as stream:
    soup = BeautifulSoup(stream.read(), 'lxml')

# extract the table into a csv
writer = csv.writer(sys.stdout)
table = soup.find("table")
for i, tr in enumerate(table.find_all("tr")):

    if i == 0:
        tag_name = "th"
    else:
        tag_name = "td"

    row = []
    for element in tr.find_all(tag_name):
        s = ' '.join([s for s in element.strings])
        row.append(' '.join(s.split()))

    # make sure to get the SEC filings link
    if i > 0:
        row[2] = tr.find_all(tag_name)[2].a['href']

    writer.writerow(row)
