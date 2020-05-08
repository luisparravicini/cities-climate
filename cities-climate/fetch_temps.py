from bs4 import BeautifulSoup
import pandas as pd
import re
import requests
from progress.bar import IncrementalBar
import mwparserfromhell
from .cache import Cache


def to_fahrenheit_int(celsius):
    return celsius * 9 / 5 + 32


min_temp = to_fahrenheit_int(10)
hi_temp = None
month = 'January'

session = requests.Session()
cache = Cache('~/download.cache')
url = 'https://www.weatherbase.com/vacation/step3.php3'
params = {'month': month, 'low': min_temp, 'hi': hi_temp}

print(f'fetching temps for {month}... ', end='', flush=True)
data = cache.get(session, url, params)
soup = BeautifulSoup(data, 'html.parser')
total = 0
queue = list()
for link in soup.find_all('a'):
    href = link['href']
    if not href.startswith('/vacation/step4'):
        continue

    queue.append(href)

    match = re.search(r'\((\d+)\)', link.next_sibling)
    n = int(match[1]) if match else 0
    total += n

print(total)
