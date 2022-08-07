import urllib.request
from selenium import webdriver
from selenium.webdriver.common.by import By
import os

# Get species name from user
species = input("Enter species name: ")

# Open Browser
browser = webdriver.Chrome()
browser.get('https://media.ebird.org/catalog')


# Find the search box
search_box = browser.find_element(by=By.ID, value="taxonFinder")
search_box.send_keys(species)

# Wait for search results
browser.implicitly_wait(1)

# Click the first result
suggestion0 = browser.find_element(by=By.ID, value="Suggest-suggestion-0")
suggestion0.click()

# Change to grid view
grid_button = browser.find_element(by=By.XPATH,
                                   value='//*[@id="content"]/div/div/form/div[1]/div[2]/div[5]/div/a[2]/span')
grid_button.click()

# Locate the first 30 photos and download them
os.mkdir(species)
for i in range(1, 31):
    xpath = '//*[@id="content"]/div/div/form/ol/li[' + str(i) + ']/div[1]/div/img'
    img = browser.find_element(By.XPATH, xpath)
    src = img.get_attribute('src')
    # Create the file
    file_name = str(species + "\\" + str(i) + ".jpg")
    urllib.request.urlretrieve(src, file_name)

# grid format
#
# //*[@id="content"]/div/div/form/ol/li[1]/div[1]/div/img
# //*[@id="content"]/div/div/form/ol/li[2]/div[1]/div/img
# //*[@id="content"]/div/div/form/ol/li[4]/div[1]/div/img
# //*[@id="content"]/div/div/form/ol/li[30]/div[1]/div/img
# //*[@id="content"]/div/div/form/ol/li[31]/div[1]/div/img
# //*[@id="content"]/div/div/form/ol/li[61]/div[1]/div/img
# list format
# //*[@id="content"]/div/div/form/ol/li[1]/div[2]/div/div/img
# //*[@id="content"]/div/div/form/ol/li[30]/div[2]/div/div/img