from requests import get
from bs4 import BeautifulSoup
import pandas as pd
from random import randint
from time import sleep

url = 'https://www.linkedin.com/'

response = get(url)
soup = BeautifulSoup(response.text, 'html.parser')
print(soup)
tagline = soup.findAll('h2')
print(tagline)