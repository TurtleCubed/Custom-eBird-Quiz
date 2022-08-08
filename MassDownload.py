import urllib.request
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import os
import datetime



# Grab species list
if not os.path.isfile("species.txt"):
    raise FileNotFoundError("no species.txt file found")
f = open("species.txt")
species_list = f.readlines()
for i in range(len(species_list)):
    species_list[i] = species_list[i][:-1]

# Pull images from each species
# Open Browser
browser = webdriver.Chrome()
browser.get('https://media.ebird.org/catalog')
if not os.path.isdir("PhotoLibrary"):
    os.mkdir("PhotoLibrary")
time1 = datetime.datetime.now()
path = "PhotoLibrary\\"
for species in species_list:
    if not os.path.isdir(str(path + "\\" + species)):
        os.mkdir(str(path + "\\" + species))
    # Find the search box
    search_box = browser.find_element(by=By.ID, value="taxonFinder")
    for i in range(60):
        search_box.send_keys(Keys.BACKSPACE)
    search_box.send_keys(species)
    # Wait for search results
    browser.implicitly_wait(5)
    # Click the first result
    suggestion0 = browser.find_element(by=By.ID, value="Suggest-suggestion-0")
    suggestion0.click()
    # Change to grid view
    grid_button = browser.find_element(by=By.XPATH,
                                       value='//*[@id="content"]/div/div/form/div[1]/div[2]/div[5]/div/a[2]/span')
    grid_button.click()
    # Locate the indexed photos and download them
    browser.implicitly_wait(5)
    for i in range(1, 31):
        xpath = '//*[@id="content"]/div/div/form/ol/li[' + str(i) + ']/div[1]/div/img'
        img = browser.find_element(By.XPATH, xpath)
        src = img.get_attribute('src')
        # Create the file
        file_name = str(path + "\\" + species + "\\" + str(i) + ".jpg")
        urllib.request.urlretrieve(src, file_name)
