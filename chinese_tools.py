import requests
import re
from bs4 import BeautifulSoup


def has_chinese_char(word):
    if word is None:
        return False
    for char in word:
        if bool(re.match('[\u4e00-\u9fff]', char)) == 0:
            return False
    return True


def searchWord(word):
    url = f'https://www.trainchinese.com/v2/search.php?searchWord={word}&rAp=0&height=0&width=0&tcLanguage=ru'
    response = requests.get(url)

    if response.status_code == 200:
        # Parse the page content using BeautifulSoup
        soup = BeautifulSoup(response.content, 'html.parser')

        rows = soup.find_all('tr')
        cells = rows[0].find_all('div')  # Again, assuming the text is in table data cells
        if cells:
            return cells[1].text[1::], cells[2].text.replace("\"", "")


from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import re
import time


def sort_elements(element):
    pos = element.location
    return (pos['x'], pos['y'])


from contextlib import contextmanager


@contextmanager
def managed_driver():
    chrome_options = Options()
    options = Options()

    chrome_options.add_argument("--page-load-strategy=none")
    chrome_options.add_argument('--ignore-certificate-errors-spki-list')
    chrome_options.add_experimental_option(
        "prefs", {
            # block image loading
            "profile.managed_default_content_settings.images": 2,
        }
    )
    # chrome_options.add_argument("--disable-javascript")
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--disable-gpu')
    driver = webdriver.Chrome(options=chrome_options)
    try:
        yield driver
    finally:
        driver.quit()


def decomposeWord(char):
    start_time = time.time()

    try:
        with managed_driver() as driver:
            # print("opened character", char)
            # print(datetime.now())
            driver.get(f'https://www.mdbg.net/chinese/dictionary?cdqchc={char}')
            print("driver opened")
            # Находим элемент с тремя точками
            hover_element = driver.find_elements(by=By.XPATH, value="//div[@class = 'c']")[0].find_element(by=By.CLASS_NAME,
                                                                                                           value="dark-invert")
            # hover_element =WebDriverWait(driver, 3).until(EC.presence_of_element_located((By.XPATH,
            #                                                                              "//div[contains(concat(" ", normalize-space(@class), " "), 'c')]")))

            # print("hover_element", datetime.now())
            ActionChains(driver).move_to_element(hover_element).perform()
            # print("moved", datetime.now())
            # Ждем, пока появится элемент кнопка элемент
            new_element = WebDriverWait(driver, 3).until(EC.presence_of_element_located((By.CSS_SELECTOR,
                                                                                         "#contentarea > table > tbody > tr > td > table > tbody > tr:nth-child(1) > td.actions > div > div > div.e > div > a:nth-child(1)")))
            # Выполняем действие с новым элементом (например, щелчок)
            # print("new_element", datetime.now())
            new_element.click()
            # print("click", datetime.now())

            WebDriverWait(driver, 3).until(
                EC.text_to_be_present_in_element((By.CLASS_NAME, "resultswrap"), "Character decomposition"))
            # print("Decomposition window opened :", end="")
            # Найти элемент, в котором нужно искать другие элементы
            parent_element = driver.find_element(by=By.XPATH,
                                                 value="//*[@id='contentarea']/table/tbody/tr/td/table/tbody/tr[2]")
            # # Найти все дочерние элементы внутри parent_element с помощью XPath
            child_elements = parent_element.find_elements(by=By.XPATH, value="//span[@class = 'char']")
            child_elements = sorted(child_elements, key=sort_elements)
            # # Вывести найденные дочерние элементы
            parent_element.location_once_scrolled_into_view
            ans = [element.text for element in child_elements]
            end_time = time.time()
            print(f"Выполнено за {end_time - start_time} секунд")
    except Exception as e:
        print(char, "caught exception:", e)
        ans = []
    return ans
