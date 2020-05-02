import csv
from pathlib import Path
import json
import pandas as pd
import re
import mpu


def read_cities_list(path):
    with open(path) as file:
        reader = csv.DictReader(file)
        return list(reader)

"city","city_ascii","lat","lng","country","population"

regions = list()
with open('Koeppen-Geiger-ASCII.txt') as file:
    # header
    file.readline()
    for _, line in enumerate(file):
        datum = re.findall(r'\S+', file.readline())
        datum[0] = float(datum[0])
        datum[1] = float(datum[1])

        datum = ((datum[0], datum[1]), datum[2])
        regions.append(datum)

print(len(regions), 'regions')
df = pd.csv('simplemaps_worldcities_basicv1.6/worldcities.csv')
print(len(df))
cities = read_cities_list('simplemaps_worldcities_basicv1.6/worldcities.csv')

path = Path('cities.json')
if path.exists():
    with open('cities.json') as file:
        cities = json.load(file)

for index, city in enumerate(cities):
    if 'koppen' in city:
        continue

    city_pos = (float(city['lat']), float(city['lng']))
    nearest = min(regions,
                  key=lambda x: mpu.haversine_distance(city_pos, x[0]))

    city['koppen'] = nearest[1]
    print(city['city'], city['koppen'], ' (%.2f%%)' % (100 * float(index) / len(cities)))

    if index % 100 == 0:
        print("\nsaving\n")
        with open('cities.json', 'w') as file:
            json.dump(cities, file)

with open('cities.json', 'w') as file:
    json.dump(cities, file)
