import urllib.request
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import os
from PIL import Image
import datetime

# Grab species list
# if not os.path.isfile("species.txt"):
#     raise FileNotFoundError("no species.txt file found")
# f = open("species.txt")
# species_list = f.readlines()
# for i in range(len(species_list)):
#     species_list[i] = species_list[i][:-1]

n = 100


# Pull images from each species
# Open Browser
def get_imgs(n):
    browser = webdriver.Chrome(ChromeDriverManager().install())
    browser.get('https://media.ebird.org/catalog?mediaType=photo&sort=id_asc&view=grid')
    if not os.path.isdir("PhotoLibrary"):
        os.mkdir("PhotoLibrary")
    time1 = datetime.datetime.now()
    path = "PhotoLibrary\\"
    for species in species_list:
        # Locate the indexed photos and download them
        browser.implicitly_wait(5)
        for i in range(1, 31):
            xpath = '//*[@id="content"]/div/div/form/ol/li[' + str(i) + ']/div[1]/div/img'
            img = browser.find_element(By.XPATH, xpath)
            src = img.get_attribute('src')
            # Create the file
            file_name = str(path + "\\" + species + "\\" + str(i) + ".jpg")
            urllib.request.urlretrieve(src, file_name)
