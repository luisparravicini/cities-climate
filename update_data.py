import requests
from pathlib import Path
import pandas as pd
import hashlib
import json
import re
from progress.bar import IncrementalBar


class Cache:
    def __init__(self, data_path):
        self.path = Path(data_path).expanduser()
        self.path.mkdir(parents=True, exist_ok=True)

    def get(self, session, url, params={}):
        cache_object_path = self._path_for(url, params)
        if cache_object_path.exists():
            return self._read(cache_object_path)

        res = session.get(url=url, params=params)
        res.raise_for_status()
        data = res.text

        self._save(cache_object_path, data)

        return data

    def get_json(self, session, url, params={}):
        data = self.get(session, url, params)
        return json.loads(data)

    def _read(self, path):
        with open(path) as file:
            return file.read()

    def _save(self, path, data):
        tmp_path = path.with_suffix('.tmp')
        with open(tmp_path, 'w') as file:
            file.write(data)
        tmp_path.rename(path)

    def _path_for(self, url, params):
        query_data = (url + str(params)).encode('utf-8')
        digest = hashlib.sha256(query_data).hexdigest()
        path = Path(self.path, digest[0:2], digest)
        path.parent.mkdir(parents=True, exist_ok=True)

        return path


def to_meters(feet):
    return feet * 0.3048


def extract_elevation(data):
    values = dict()
    for line in data.split("\n"):
        # print(line)
        match = re.match(r'\| elevation_(\S+)\s*=\s*([\d,]+)', line)
        if match is None:
            continue

        parts = match[1].split('_')
        if len(parts) > 2:
            print(f'\nError parsing elevation for {name}: "{parts}"')
            return 0

        if len(parts) == 1:
            unit = parts[0]
            key = ''
            if unit == 'min' or unit == 'max':
                key = unit
                unit = 'm'
        else:
            key, unit = parts

        value = match[2].replace(',', '')
        if len(value) == 0:
            print(f'\nNo elevation value found for: {name}')
            return 0

        if key not in values:
            values[key] = dict()
        values[key][unit] = int(value)

    if len(values) == 0:
        return 1

    elevations = dict()
    for key, value in values.items():
        if 'ft' in value:
            x = int(to_meters(value['ft']))
        else:
            if 'm' in value:
                x = value['m']
            else:
                print(values)
                print(f'Unknown elevation: "{value}"')
                return 0

        elevations[key] = x
    # print(elevations)

    return 0


def extract_climate_from_box(data):
    months = (
        'year',
        'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec',
        'yeard',
        'Jand', 'Febd', 'Mard', 'Aprd', 'Mayd', 'Jund', 'Juld', 'Augd', 'Sepd', 'Octd', 'Novd', 'Decd'
    )
    prefix_blacklist = (
        'unit precipitation days',
        'unit rain days',
        'unit snow days',
        'pages',
        'page',
        'time day',
        'open',
        'metric first'
    )
    first_item_blacklist = (
        'accessdate', 'access-date', 'archivedate',
        'width', 'archive-date', 'time day', 'date'
    )
    for line in data.split("\n"):
        line = line.replace('−', '-')
        match = re.match(r'\s*\|([^=]+)=\s*(-?[\d\.]+)', line, flags=re.IGNORECASE)
        if match is not None:
            prefix = match[1].strip()
            if prefix in prefix_blacklist:
                continue

            items = match[1].strip().split(' ')
            value = match[2]
            first_item = items[0]
            if first_item in first_item_blacklist:
                continue

            if first_item not in months:
                print()
                print(f'"{match[1]}" "{line}"')
            # print(match)


def extract_climate(data):
    weather_boxes = re.findall(r'\{\{Weather box.*?(?:\n\}\}|\}\}\n)', data, re.DOTALL)
    # for weather in weather_boxes:
    #     print(weather)
    if len(weather_boxes) == 0:
        return 1

    for box in weather_boxes:
        extract_climate_from_box(box)
    return 0


def find_city_url(session, cache, city):
    base_url = "https://en.wikipedia.org/w/api.php"

    params = {
        "action": "opensearch",
        "namespace": "0",
        "search": city,
        "limit": "5",
        "format": "json"
    }

    data = cache.get_json(session, base_url, params)

    titles = data[1]
    urls = data[-1]
    results = filter(lambda x: x[0].lower() == city.lower(),
                     zip(titles, urls))
    results = list(results)
    return results[0][1] if (len(results) > 0) else None


cities_path = 'cities.csv'
cities_df = pd.read_csv(cities_path)

print(len(cities_df), 'cities')
print()

cache = Cache('~/download.cache')
session = requests.Session()
bar = IncrementalBar('City', max=len(cities_df))
climate_box_not_found = 0
elevation_not_found = 0
for _, city in cities_df.iterrows():
    name = city['city']
    bar.message = name[0:30].ljust(30)
    bar.next()
    koppen = city['koppen']

    if not koppen.startswith('C'):
        continue

    url = find_city_url(session, cache, name)
    if url is None:
        continue

    params = {'action': 'raw'}
    data = cache.get(session, url, params)
    # print(cache._path_for(url, params))

    elevation_not_found += extract_elevation(data)
    climate_box_not_found += extract_climate(data)


bar.finish()

print()
print(f'elevation not found: {elevation_not_found}')
print(f'weather box not found: {climate_box_not_found}')
