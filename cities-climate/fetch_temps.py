from bs4 import BeautifulSoup
import pandas as pd
import re
import requests
from progress.bar import IncrementalBar
import mwparserfromhell
from .cache import Cache
from urllib.parse import urljoin, urlparse


def to_fahrenheit_int(celsius):
    return celsius * 9 / 5 + 32


def fetch_cities_data(cache, session, url):
    data = list()

    url += '&set=metric'

    page_content = cache.get(session, url)
    # need to use html5lib as the html is malformed and
    # it needs a more lenient parser than the default one
    soup = BeautifulSoup(page_content, 'html5lib')

    # or state if inside USA
    country = soup.find('h1').text.split('-')[-1].strip().capitalize()

    table = soup.find('div', {'id': 'left-content'}).find('table')
    for row in table.find_all('tr')[1:]:
        cells = row.find_all('td')
        if len(cells) != 7:
            continue

        datum = list(map(lambda x: x.text, cells))
        datum.insert(1, country)
        data.append(datum)

    return data


def to_bar_message(s):
    return s[0:30].ljust(30)


def fetch_month(month, session, cache, min_temp, max_temp):
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

            bar.message = to_bar_message(link.get_text())

            temps = fetch_cities_data(cache, session, href)

            # next forces the bar to refresh (it's needed for the message)
            bar.next(0)

        bar.next(amount)

    bar.finish()


session = requests.Session()
cache = Cache('~/download.cache')
min_temp = to_fahrenheit_int(10)
max_temp = None
print(f'collecting cities with temperature range: {min_temp}-{max_temp}')
months = ('January', 'February', 'March', 'April',
          'May', 'June', 'July', 'August', 'September',
          'October', 'November', 'December')
for month in months:
    fetch_month(month, session, cache, min_temp, max_temp)
    print()
