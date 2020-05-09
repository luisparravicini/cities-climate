from bs4 import BeautifulSoup
import pandas as pd
import re
import requests
from progress.bar import IncrementalBar
from pathlib import Path
import mwparserfromhell
from .cache import HttpCache, DataCache
from urllib.parse import urljoin, urlparse
import pandas as pd


def to_fahrenheit_int(celsius):
    if celsius is None:
        return None

    return int(celsius * 9 / 5 + 32)


def parse_cities_data(soup, data):
    # or state if inside USA
    country = soup.find('h1').text.split('-')[-1].strip().capitalize()

    table = soup.find('div', {'id': 'left-content'}).find('table')
    for row in table.find_all('tr')[1:]:
        cells = row.find_all('td')
        if len(cells) != 7:
            continue

        datum = list(map(lambda x: x.text, cells))

        href = cells[0].find('a')['href']
        match = re.search(r'\?s=(\d+)', href)
        id = match[1] if match else None
        datum.append(id)

        datum.insert(1, country)

        data.append(datum)


def fetch_cities_data(cache, session, url):
    data = list()

    page_content = cache.get(session, url)

    # In some cases, a country is listed, but following the link returns
    # an error (also happens when manually navigating usinh a browser)
    if 'You must first choose a month to find' not in page_content:
        # need to use html5lib as the html is malformed and
        # it needs a more lenient parser than the default one
        soup = BeautifulSoup(page_content, 'html5lib')
        parse_cities_data(soup, data)

    return data


def to_bar_message(s):
    return s[0:30].ljust(30)


def fetch_month(month, session, cache, min_temp, max_temp, data_cache):
    url = 'https://www.weatherbase.com/vacation/step3.php3'
    params = {'month': month, 'low': min_temp, 'hi': max_temp}

    print(f'fetching temps for {month}...')
    data = cache.get(session, url, params)
    soup = BeautifulSoup(data, 'html.parser')
    total = 0
    queue = list()
    for link in soup.find_all('a'):
        href = urljoin(url, link['href'])
        if not urlparse(href).path.startswith('/vacation/step4'):
            continue

        match = re.search(r'\((\d+)\)', link.next_sibling)
        n = int(match[1]) if match else 0

        queue.append((href, link.get_text(), n))

        total += n

    bar = IncrementalBar('fetching', max=total)
    while len(queue) > 0:
        url, name, amount = queue.pop()
        bar.message = to_bar_message(name)

        data = cache.get(session, url)
        soup = BeautifulSoup(data, 'html.parser')
        for link in soup.find_all('a'):
            href = urljoin(url, link['href'])
            if not urlparse(href).path.startswith('/vacation/step5'):
                continue
            href += '&set=metric'

            bar.message = to_bar_message(link.get_text())
            if not data_cache.has(href):
                cities_data = fetch_cities_data(cache, session, href)
                for datum in cities_data:
                    datum.append(month)
                data_cache.save_json(href, list(cities_data))

            # next forces the bar to refresh (it's needed for the message)
            bar.next(0)

        bar.next(amount)

    bar.finish()


def fetch_all_temps(data_cache, min_temp, max_temp):
    session = requests.Session()
    cache = HttpCache('~/download.cache')
    print(f'collecting cities info')
    months = ('January', 'February', 'March', 'April',
              'May', 'June', 'July', 'August', 'September',
              'October', 'November', 'December')
    min_temp = to_fahrenheit_int(min_temp)
    max_temp = to_fahrenheit_int(max_temp)
    for month in months:
        fetch_month(month, session, cache, min_temp, max_temp, data_cache)
        print()


def clean_row(datum):
    return map(lambda row:
               map(lambda x: re.sub(r' °C| mm|---', '', x), row),
               datum)


def parse_all_temps(data_cache, results_path):
    print('Collecting temps')
    weather_rows = list()
    data_cache.for_each(lambda x: weather_rows.extend(clean_row(x)))
    cols = ['City', 'Country', 'Avg temp', 'Avg high', 'Avg low',
            'Avg rainy days', 'Avg rainfall', 'Avg snowfall', 'City id', 'Month']
    weather_df = pd.DataFrame(weather_rows, columns=cols)
    weather_df.drop_duplicates(inplace=True)

    weather_df.to_csv(results_path, index=False)
    print(f'Saved temps in "{results_path}"')


data_cache = DataCache('weather.cache')
csv_path = Path('weather_info.csv')
if not csv_path.exists():
    fetch_all_temps(data_cache, min_temp=None, max_temp=None)
    parse_all_temps(data_cache, csv_path)
else:
    print(f'using already collected data in "{csv_path}"')

min_temp = 0
max_temp = 60
df = pd.read_csv(csv_path)
df_temp_range = df[(df['Avg low'] >= min_temp) & (df['Avg high'] < max_temp)]
df_by_month = df_temp_range.groupby(['City id', 'City', 'Country'])['Month'].count().sort_values()
print(df_by_month.to_string())

# print(df.to_string())
# print(df[df['City'] == 'Arakoon'].to_string())
