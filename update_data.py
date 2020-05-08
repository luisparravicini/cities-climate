import requests
from pathlib import Path
import pandas as pd
import hashlib
import json
import re
from progress.bar import IncrementalBar
import mwparserfromhell


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
        'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec',
    )
    daily_sunshine_months = (
        'Jand', 'Febd', 'Mard', 'Aprd', 'Mayd', 'Jund', 'Juld', 'Augd', 'Sepd', 'Octd', 'Novd', 'Decd'
    )
    prefix_blacklist = (
        'unit precipitation days',
        'unit rain days',
        'unit snow days',
        'Year snow days',
        'Year rain days',
    )

    keys = set()
    wikicode = mwparserfromhell.parse(data)
    for template in wikicode.filter_templates():
        if template.name != 'Weather box':
            continue

        for param in template.params:
            name = param.name.strip()
            if name in prefix_blacklist:
                continue

            name = name.split(' ', maxsplit=1)
            if len(name) == 1:
                continue

            month, key = name
            if month.startswith('year'):
                continue

            value = param.value.strip().replace('−', '-')

            # TODO: assuming "sunshine hours" and "daylight hours" are the same
            # I don't know whether that's correct
            if month in daily_sunshine_months:
                # using 30 for days in month
                value = str(float(value) * 30)
                month = month[0:-1]

            if month in months:
                value = None if value == '' else float(value)
                # I'm assuming the units are always in the metric system
                if key.endswith(' C'):
                    key = key[:-2]
                if key.endswith(' mm'):
                    key = key[:-3]                

                keys.add(key)


                # print(f'/{month}/{key}/{value}')

    return keys


def extract_climate(data):
    weather_boxes = re.findall(r'\{\{Weather box.*?(?:\n\}\}|\}\}\n)', data, re.DOTALL)
    keys = set()

    if len(weather_boxes) == 0:
        return (1, keys)

    for box in weather_boxes:
        keys |= extract_climate_from_box(box)

    return (0, keys)


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
all_weather_keys = set()
for _, city in cities_df.iterrows():
    name = city['city']
    bar.message = name[0:30].ljust(30)
    bar.next()

    koppen = city['koppen']
    if not koppen.startswith('C'):
        continue

    if city['country'] == 'United States':
        continue

    url = find_city_url(session, cache, name)
    if url is None:
        continue

    params = {'action': 'raw'}
    data = cache.get(session, url, params)
    # print(cache._path_for(url, params))

    elevation_not_found += extract_elevation(data)
    boxes_found, weather_keys = extract_climate(data)
    climate_box_not_found += boxes_found
    all_weather_keys |= weather_keys


bar.finish()

print()
print(f'elevation not found: {elevation_not_found}')
print(f'weather box not found: {climate_box_not_found}')
print('weather keys: ', all_weather_keys)
