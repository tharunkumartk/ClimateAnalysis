from bs4 import BeautifulSoup
import requests as req
import csv
URL = 'https://txcip.org/tac/census/morecountyinfo.php?MORE=1005'
page = req.get(URL)
soup = BeautifulSoup(page.content, 'lxml')
lists_data = soup.select('td')
records = []
record = []
for row in lists_data[1:]:
    record.append(row.text)
    if len(record) == 2:
        records.append(record)
        record = []
filename = 'county_area.csv'
with open(filename, 'w') as csvfile:
    csvwriter = csv.writer(csvfile)
    for row in records:
        csvwriter.writerow(row)