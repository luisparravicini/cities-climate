This repo has several scripts, all related to cities temperatures, maybe some overlapping another's functionality:

For all the scripts you need first to install dependencies with:

`pip install --user -r requeriments.txt`


## Finding Köppen climate classification

Given a list of cities with their latitude and longitude, the script finds (approximately) the city's [Koppen climate classification](https://en.wikipedia.org/wiki/K%C3%B6ppen_climate_classification).
To do this it uses a "world map" divided in 0.5 degree zones and finds the nearest zone for a city position.

### Running

Download the data files (the ones listed in *Data Sources*) and put them in `data/`

Run the script:

`python -m cities-climate.find_cities_koppen`

It initially reads the cities list from `data/` and then it will start saving all the intermediate (and final) data in `cities.csv`.

### Data sources

* [Cities list from simplemaps](https://simplemaps.com/data/world-cities)
* [Koppen climate map](http://koeppen-geiger.vu-wien.ac.at/data/Koeppen-Geiger-ASCII.zip) from [World maps of Köppen-Geiger climate classification](http://koeppen-geiger.vu-wien.ac.at/present.htm). That file has a resolution of 0.5 degree and for the 50-year period 1951-2000.


## List of cities within a temperature range

Given a temperature range it lists cities having at least one month where their monthly average temperature falls within this range.

### Running

Run the script:

`python -m cities-climate.fetch_temps --min MIN_TEMP --max MAX_TEMP`

It initially scrapes data from WeatherBase and builds a local cache, so the script can resume from where it left off if interrupted. After downloading all the data, it saves a .csv file with all the data.

## List of cities within a temperature range (2)

Given a temperature range it lists cities having average monthly temperature in that range for all the year.

### Running

Run the script:

`python -m cities-climate.wikipedia_temps --min MIN_TEMP --max MAX_TEMP`

This script uses data from a wikipedia article listing average temps for several cities around the world. After downloading and parsing, the data is stored in a csv file.

There's also a small vue web app that uses this info to show the list of cities within certain range, to run it:

`cd temps; npm run serve`
