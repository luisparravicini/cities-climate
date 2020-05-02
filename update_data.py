import csv
from bs4 import BeautifulSoup
import requests
from pathlib import Path
import hashlib
import json


def read_cities_list(path):
    with open(path) as file:
        reader = csv.DictReader(file)
        return list(reader)


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


cache = Cache('~/download.cache')
cities = read_cities_list('simplemaps_worldcities_basicv1.6/worldcities.csv')
print(len(cities), 'cities')
session = requests.Session()
for city in cities:
    name = city['city']
    print(name + ' [', end='', flush=True)

    print('.', end='', flush=True)
    url = find_city_url(session, cache, name)
    if url is None:
        print("\x08X ]")
        continue
    print("\x08o", end='', flush=True)

    print('.', end='', flush=True)
    data = cache.get(session, url)
    # soup = BeautifulSoup(html_doc, 'html.parser')
    print("\x08o", end='', flush=True)


    print("]")
