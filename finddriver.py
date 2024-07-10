import logging
from selenium import webdriver
from selenium.webdriver.chrome.service import Service

# Set up logging
logging.basicConfig(level=logging.DEBUG)

# Create a new ChromeDriver service with verbose logging
service = Service(log_path='chromedriver.log', verbose=True)

# Create a new Chrome driver instance
driver = webdriver.Chrome(service=service)

driver.quit()