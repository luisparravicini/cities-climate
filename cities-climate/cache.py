import hashlib
import json
import requests
from pathlib import Path


class BaseCache:
    def __init__(self, data_path):
        self.path = Path(data_path).expanduser()
        self.path.mkdir(parents=True, exist_ok=True)

    def _read(self, path):
        with open(path) as file:
            return file.read()

    def _save(self, path, data):
        tmp_path = path.with_suffix('.tmp')
        with open(tmp_path, 'w') as file:
            file.write(data)
        tmp_path.rename(path)

    def _path_for(self, url):
        query_data = url.encode('utf-8')
        digest = hashlib.sha256(query_data).hexdigest()
        path = Path(self.path, digest[0:2], digest)
        path.parent.mkdir(parents=True, exist_ok=True)

        return path


class HttpCache(BaseCache):
    def __init__(self, data_path):
        super().__init__(data_path)

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

    def _save(self, path, data):
        tmp_path = path.with_suffix('.tmp')
        with open(tmp_path, 'w') as file:
            file.write(data)
        tmp_path.rename(path)

    def _path_for(self, url, params):
        return super()._path_for(url + str(params))


class DataCache(BaseCache):
    def __init__(self, data_path):
        super().__init__(data_path)

    def for_each(self, processor):
        for file_path in Path(self.path).rglob('*'):
            if not file_path.is_file():
                continue
            processor(json.loads(self._read(file_path)))

    def has(self, key):
        cache_object_path = self._path_for(key)
        return cache_object_path.exists()

    def read(self, key):
        if self.has(key):
            cache_object_path = self._path_for(key)
            return self._read(cache_object_path)

        return None

    def get_json(self, session, key):
        data = self.get(session, key)
        return json.loads(data)

    def save_json(self, key, data):
        cache_object_path = self._path_for(key)
        self._save(cache_object_path, json.dumps(data))
