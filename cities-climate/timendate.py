from bs4 import BeautifulSoup
import pandas as pd
import re
import requests
from progress.bar import IncrementalBar
from pathlib import Path
from .cache import HttpCache, DataCache
from urllib.parse import urljoin, urlparse, urlunparse
import argparse
import json


def to_bar_message(s):
    return s[0:30].ljust(30)


def parse_country(cities_urls, url, name, data):
    soup = BeautifulSoup(data, 'html.parser')
    for link in soup.find_all('a', href=True):
        href = urljoin(url, link['href'])
        if not urlparse(href).path.startswith('/weather/' + name + '/'):
            continue

        if href not in cities_urls:
            cities_urls.append(href)


def fetch_countries(cache, session, urls):
    cities_urls = list()
    bar = IncrementalBar('fetching', max=len(urls))
    for url in urls:
        name = urlparse(url).path.split('/')[-1]
        bar.message = to_bar_message(name)
        # next forces the bar to refresh (it's needed for the message)
        bar.next(0)

        data = cache.get(session, url, params=None)
        parse_country(cities_urls, url, name, data)

        bar.next()

    bar.finish()
    return cities_urls


def parse_city(name, data):
    datum = {}

    m = re.search(r'var data=({.*?});', data)
    if not m:
        print("\ncouldn't find temps!")
        return None
    datum['temps'] = json.loads(m[1])

    m = re.search(r'TAD.lon=([\d\.-]+);TAD.lat=([\d\.-]+);', data)
    if not m:
        print("\ncouldn't find pos")
        return None
    datum['pos'] = { 'lat': m[1], 'lng': m[2] }
    
    soup = BeautifulSoup(data, 'html.parser')
    m = re.search(' in (.*?)$', soup.find('title').text)
    if not m:
        print("\ntitle not found")
        return None    
    name = list(map(lambda x: x.strip(), m[1].split(',')))
    if len(name) < 2:
        print(f"\nunknown name format: '{name}'")
        return None
    datum['name'] = { 'city': name[0], 'country': name[-1] }

    return datum


def fetch_cities(cache, session, urls):
    cities_data = list()
    bar = IncrementalBar('fetching', max=len(urls))
    for url in urls:
        name = urlparse(url).path.split('/')[-1]
        bar.message = to_bar_message(name)
        # next forces the bar to refresh (it's needed for the message)
        bar.next(0)

        url += '/climate'
        data = cache.get(session, url, params=None)
        datum = parse_city(name, data)
        if datum is not None:
            cities_data.append(datum)
            # print(datum)

        bar.next()

    bar.finish()
    return data


def fetch_all_temps(data_cache):
    session = requests.Session()
    cache = HttpCache('~/download.cache')
    print(f'collecting countries list')
    url = 'https://www.timeanddate.com/weather/?low=c'
    data = cache.get(session, url)
    soup = BeautifulSoup(data, 'html.parser')
    links = list()
    for link in soup.find_all('a'):
        href = urlparse(urljoin(url, link['href']))
        if not href.path.startswith('/weather'):
            continue
        parts = href.path.split('/')
        if len(parts) != 4:
            continue
        
        # oops, bad link
        if parts[2] == 'kazakstan':
            parts[2] = 'kazakhstan'
        href = urlunparse(href._replace(path='/'.join(parts[0:3])))
        if href not in links:
            links.append(href)

    cities_urls = fetch_countries(cache, session, links)
    data = fetch_cities(cache, session, cities_urls)



def clean_rows(datum):
    return map(lambda row: clean_row(row), datum)


def parse_all_temps(data_cache, results_path):
    print('Collecting temps')
    weather_rows = list()
    data_cache.for_each(lambda x: weather_rows.extend(clean_rows(x)))

    cols = ['City', 'Country', 'Avg temp', 'Avg high', 'Avg low',
            'Avg rainy days', 'Avg rainfall', 'Avg snowfall', 'City id',
            'Month']
    weather_df = pd.DataFrame(weather_rows, columns=cols)

    weather_df['Avg temp'] = (weather_df['Avg low'] + weather_df['Avg high']) / 2
    weather_df = weather_df.drop_duplicates(['City id', 'Month'])

    weather_df.to_csv(results_path, index=False)
    print(f'Saved temps in "{results_path}"')


parser = argparse.ArgumentParser(description='List cities temperatures')
parser.add_argument('--max', dest='max', type=int,
                    help='maximum (including) temperature')
parser.add_argument('--min', dest='min', type=int,
                    help='mininum (including) temperature')

args = parser.parse_args()
min_temp = args.min or -200
max_temp = args.max or 200

data_cache = DataCache('timendate.cache')
csv_path = Path('timendate.csv')
if not csv_path.exists():
    fetch_all_temps(data_cache)
    parse_all_temps(data_cache, csv_path)
else:
    print(f'using collected data in "{csv_path}"')

df = pd.read_csv(csv_path)

df_temp_range = df[(df['Avg low'] >= min_temp) & (df['Avg high'] < max_temp)]
df_by_month = df_temp_range.groupby(['City id', 'City', 'Country'])['Month'].count().sort_values()

print(df_by_month.to_string())

