Given a list of cities with their latitude and longitude, the script finds (approximately) the city [Koppen climate classification](https://en.wikipedia.org/wiki/K%C3%B6ppen_climate_classification).
To do this it uses a "world map" divided in 0.5 degree zones and finds the nearest zone for a city position.

## Running

Install dependencies:

`pip install --user -r requeriments.txt`

Download the data files (the ones listed in *Data Sources*) and put them in `data/`

Run the script:

`python -m cities-climate.find_cities_koppen`

It initially reads the cities list from `data/` and then it will start saving all the intermediate (and final) data in `cities.csv`.



## Data sources

* [Cities list from simplemaps](https://simplemaps.com/data/world-cities)
* [Koppen climate map](http://koeppen-geiger.vu-wien.ac.at/data/Koeppen-Geiger-ASCII.zip) from [World maps of Köppen-Geiger climate classification](http://koeppen-geiger.vu-wien.ac.at/present.htm). That file has a resolution of 0.5 degree and for the 50-year period 1951-2000.

