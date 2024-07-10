import requests
import json
import os
import zipfile
import shutil


def download_chromedriver(version, platform='win64'):
    base_url = "https://googlechromelabs.github.io/chrome-for-testing"
    version_url = f"{base_url}/known-good-versions-with-downloads.json"

    response = requests.get(version_url)
    data = json.loads(response.text)

    matching_version = next((v for v in data['versions'] if v['version'].startswith(version)), None)

    if matching_version:
        download_url = next(
            (d['url'] for d in matching_version['downloads']['chromedriver'] if d['platform'] == platform), None)

        if download_url:
            response = requests.get(download_url)
            filename = os.path.basename(download_url)

            with open(filename, 'wb') as file:
                file.write(response.content)

            with zipfile.ZipFile(filename, 'r') as zip_ref:
                zip_ref.extractall()

            # Move chromedriver to current directory
            shutil.move(os.path.join('chromedriver-win64', 'chromedriver.exe'), 'chromedriver.exe')

            # Clean up
            os.remove(filename)
            shutil.rmtree('chromedriver-win64')

            print(f"ChromeDriver {version} downloaded and extracted successfully.")
            return os.path.abspath('chromedriver.exe')
        else:
            print(f"No download URL found for ChromeDriver {version} on {platform}.")
    else:
        print(f"No matching version found for ChromeDriver {version}.")


# Download ChromeDriver
chromedriver_path = download_chromedriver("126")
print(chromedriver_path)
# Now use this path in your Selenium script
from selenium import webdriver
from selenium.webdriver.chrome.service import Service

service = Service(executable_path=chromedriver_path)
driver = webdriver.Chrome(service=service)

# Your Selenium code here...

driver.quit()