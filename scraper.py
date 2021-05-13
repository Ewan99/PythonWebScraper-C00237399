import requests
from bs4 import BeautifulSoup

URL = 'https://haveibeenpwned.com/PwnedWebsites'
page = requests.get(URL)

soup = BeautifulSoup(page.content, 'html.parser')

names = soup.find_all('h3', )

print(names)


