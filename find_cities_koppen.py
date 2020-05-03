import csv
import re
import pandas as pd
from pathlib import Path
from progress.bar import IncrementalBar


regions = dict()
with open('data/Koeppen-Geiger-ASCII.txt') as file:
    # header
    file.readline()

    for _, line in enumerate(file):
        datum = re.findall(r'\S+', file.readline())
        lat = float(datum[0])
        lng = float(datum[1])
        koppen = datum[2]

        if lat not in regions:
            regions[lat] = dict()

        regions[lat][lng] = koppen

cities_path = Path('cities.csv')
if cities_path.exists():
    cities_df = pd.read_csv(cities_path)
else:
    cities_df = pd.read_csv('data/worldcities.csv')
    cities_df = cities_df[['city', 'city_ascii', 'lat', 'lng', 'country', 'population']]
    cities_df

print(len(cities_df), 'cities')
print()

bar = IncrementalBar('City', max=len(cities_df))
for index, city in cities_df.iterrows():
    bar.message = city['city'][0:30].ljust(30)
    bar.next()
    if 'koppen' in city:
        continue

    city_pos = (city['lat'], city['lng'])
    # the "correct way" would be to calculate the Haversine distance
    # between the two points, but as there is a grid 0.5 degree, I assume
    # the error should be mininum (and it's faster with this dict of dicts)
    # than using haversine for all cells
    # mpu.haversine_distance(city_pos, x[0]))

    nearest_lat = min(regions,
                  key=lambda x: abs(city_pos[0] - x))
    nearest_lng = min(regions[nearest_lat],
                  key=lambda x: abs(city_pos[1] - x))

    cities_df.loc[index, 'koppen'] = regions[nearest_lat][nearest_lng]

    if index > 0 and index % 1000 == 0:
        bar.message = '(saving)'.ljust(30)
        cities_df.to_csv(cities_path, index_label=False)

cities_df.to_csv(cities_path, index_label=False)

bar.finish()
