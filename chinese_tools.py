import requests
import re
from bs4 import BeautifulSoup


def has_chinese_char(word):
    if word is None:
        return False
    else:
        return bool(re.search('[\u4e00-\u9fff]', word))


def searchWord(word):
    url = f'https://www.trainchinese.com/v2/search.php?searchWord={word}&rAp=0&height=0&width=0&tcLanguage=ru'
    response = requests.get(url)

    if response.status_code == 200:
        # Parse the page content using BeautifulSoup
        soup = BeautifulSoup(response.content, 'html.parser')

        rows = soup.find_all('tr')
        cells = rows[0].find_all('div')  # Again, assuming the text is in table data cells
        if cells:
            return cells[1].text[1::], cells[2].text