from bs4 import BeautifulSoup
import pandas as pd
import re
import requests
from progress.bar import IncrementalBar
from pathlib import Path
from .cache import HttpCache, DataCache
from urllib.parse import urljoin, urlparse, urlunparse
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


def parse_temps(temps):
    months_names = ["Jan", "Feb", "Mar", "Apr", "May",
                "Jun", "Jul", "Aug", "Sep", "Oct",
                "Nov", "Dec"]
    temps_data = list()
    for month in months_names:
        data = next(x for x in temps if x['name'] == month)
        data = list(map(lambda x: data[x],
                        ['min', 'max', 'mean', 'prec']))
        temps_data.append(data)

    return temps_data


def parse_city(name, data):
    datum = {}

    m = re.search(r'var data=({.*?});', data)
    if not m:
        print("\ncouldn't find temps!")
        return None
    temps = json.loads(m[1])['months']
    if len(temps) != 12:
        print(f"\nunexpected temps size: {len(temps)}")
        return None
    datum['temps'] = parse_temps(temps)

    m = re.search(r'TAD.lon=([\d\.-]+);TAD.lat=([\d\.-]+);', data)
    if not m:
        print("\ncouldn't find pos")
        return None
    datum['pos'] = [float(m[1]), float(m[2])]
    
    soup = BeautifulSoup(data, 'html.parser')
    m = re.search(' in (.*?)$', soup.find('title').text)
    if not m:
        print("\ntitle not found")
        return None    
    name = list(map(lambda x: x.strip(), m[1].split(',')))
    if len(name) < 2:
        print(f"\nunknown name format: '{name}'")
        return None
    datum['name'] = name[0]
    datum['country'] = name[-1]

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

        bar.next()

    bar.finish()
    return cities_data


def process_data(data):
    countries = list()
    for city in data['cities']:
        country = city['country']
        if country not in countries:
            countries.append(country)
        city['country'] = countries.index(country)

    data['countries'] = countries


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
    data = { 'cities': data }
    process_data(data)

    return data


def save_data(data, json_path):
    print(f'storing data at {json_path}')
    with open(json_path, 'w') as file:
        file.write(json.dumps(data))


def clean_rows(datum):
    return map(lambda row: clean_row(row), datum)


data_cache = DataCache('timendate.cache')
json_path = Path('temps/src/assets/temps.json')
if not json_path.exists():
    data = fetch_all_temps(data_cache)
    save_data(data, json_path)
else:
    print(f'data already exists at "{json_path}"')

