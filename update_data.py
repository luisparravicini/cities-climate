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

    values = dict()
    for line in data.split("\n"):
        # print(line)
        match = re.match(r'\| elevation_(\S+)\s*=\s*([\d,]+)', line)
        if match is None:
            continue

        parts = match[1].split('_')
        if len(parts) > 2:
            print(f'\nError parsing elevation for {name}: "{parts}"')
        value = match[2].replace(',', '')
        if len(value) == 0:
            print(f'\nNo elevation value found for: {name}')
        values[match[1]] = value
    # print(values)
    if len(values) == 0:
        elevation_not_found += 1

    weather_boxes = re.findall(r'\{\{Weather box.*?(?:\n\}\}|\}\}\n)', data, re.DOTALL)
    if len(weather_boxes) == 0:
        climate_box_not_found += 1
    # for weather in weather_boxes:
    #     print(weather)


bar.finish()

print()
print(f'elevation not found: {elevation_not_found}')
print(f'weather box not found: {climate_box_not_found}')
