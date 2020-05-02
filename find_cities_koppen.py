import csv
from pathlib import Path
import json
import pandas as pd
import re
import mpu
from progress.bar import IncrementalBar


def read_cities_list(path):
    with open(path) as file:
        reader = csv.DictReader(file)
        return list(reader)

# "city","city_ascii","lat","lng","country","population"

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

df = pd.read_csv('simplemaps_worldcities_basicv1.6/worldcities.csv')
# df = pd.DataFrame()
print(len(df))
cities = read_cities_list('simplemaps_worldcities_basicv1.6/worldcities.csv')

path = Path('cities.json')
if path.exists():
    with open('cities.json') as file:
        cities = json.load(file)

bar = IncrementalBar('City', max=len(cities))
for index, city in enumerate(cities):
    bar.message = city['city'][0:30].ljust(30)
    bar.next()
    if 'koppen' in city:
        continue

    city_pos = (float(city['lat']), float(city['lng']))
    nearest = min(regions,
                  key=lambda x: mpu.haversine_distance(city_pos, x[0]))

    city['koppen'] = nearest[1]
    # print(city['city'], city['koppen'], ' (%.2f%%)' % (100 * float(index) / len(cities)))

    if index % 50 == 0:
        bar.message = '(saving)'.ljust(30)
        with open('cities.json', 'w') as file:
            json.dump(cities, file)

with open('cities.json', 'w') as file:
    json.dump(cities, file)

bar.finish()
