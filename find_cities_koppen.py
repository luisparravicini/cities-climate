import csv
import re
import mpu
import pandas as pd
from pathlib import Path
from progress.bar import IncrementalBar


regions = list()
with open('data/Koeppen-Geiger-ASCII.txt') as file:
    # header
    file.readline()

    for _, line in enumerate(file):
        datum = re.findall(r'\S+', file.readline())
        regions.append((
            (float(datum[0]), float(datum[1])),
            datum[2]))

print(len(regions), 'regions')

cities_path = Path('cities.csv')
if cities_path.exists():
    cities_df = pd.read_csv(cities_path)
else:
    cities_df = pd.read_csv('data/worldcities.csv')
    cities_df = cities_df[['city', 'city_ascii', 'lat', 'lng', 'country', 'population']]

print(len(cities_df), 'cities')
print()

bar = IncrementalBar('City', max=len(cities_df))
for index, city in cities_df.iterrows():
    bar.message = city['city'][0:30].ljust(30)
    bar.next()
    if 'koppen' in city:
        continue

    city_pos = (city['lat'], city['lng'])
    nearest = min(regions,
                  key=lambda x: mpu.haversine_distance(city_pos, x[0]))

    city['koppen'] = nearest[1]

    if index > 0 and index % 50 == 0:
        bar.message = '(saving)'.ljust(30)
        cities_df.to_csv(cities_path)

cities_df.save_csv(cities_path)

bar.finish()
