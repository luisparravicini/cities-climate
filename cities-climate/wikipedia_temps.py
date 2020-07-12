from bs4 import BeautifulSoup
import pandas as pd
import re
import requests
from pathlib import Path
from .cache import HttpCache, DataCache
import numpy as np
import json
import argparse


def fetch_all_temps(data_cache, csv_path, months_names):
    url = 'https://en.wikipedia.org/wiki/List_of_cities_by_average_temperature'
    session = requests.Session()
    cache = HttpCache('~/download.cache')
    print(f'downloading cities temps')
    data = cache.get(session, url)
    soup = BeautifulSoup(data, 'html.parser')

    all_temps = list()
    for table in soup.find_all('table'):
        for row in table.find_all('tr'):
            cells = row.find_all('td')
            if len(cells) != 16:
                continue

            country_link = cells[0].find('a')
            if country_link == None:
                continue

            city_link = cells[1].find('a')
            if city_link == None:
                continue

            temps = map(lambda x:
                        x.text.replace('−', '-'),
                        cells[2:14])
            temps = map(lambda x:
                        re.sub(r'\([\d\.-]+\)', '', x),
                        temps)
            temps = map(float, temps)

            datum = list()
            datum.append(city_link.text)
            datum.append(country_link.text)
            datum.extend(temps)

            all_temps.append(datum)

    cols = ['City', 'Country'] + months_names
    df = pd.DataFrame(all_temps, columns=cols)

    df.to_csv(csv_path, index=False)
    print(f'saved temps in "{csv_path}"')


parser = argparse.ArgumentParser(description='List cities temperatures')
parser.add_argument('--max', dest='max', type=int,
                    help='maximum (including) temperature')
parser.add_argument('--min', dest='min', type=int,
                    help='mininum (including) temperature')

args = parser.parse_args()
min_temp = args.min or -200
max_temp = args.max or 200
months_names = ["Jan", "Feb", "Mar", "Apr", "May",
                "Jun", "Jul", "Aug", "Sep", "Oct",
                "Nov", "Dec"]
data_cache = DataCache('wikipedia.cache')
csv_path = Path('wikipedia.csv')
if not csv_path.exists():
    fetch_all_temps(data_cache, csv_path, months_names)
else:
    print(f'using collected data in "{csv_path}"')

df = pd.read_csv(csv_path)

filter = [df[month].between(min_temp, max_temp) for month in months_names]
print(df[np.logical_and.reduce(filter)])
