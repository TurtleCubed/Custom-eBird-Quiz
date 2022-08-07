import urllib.request
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import os
import datetime
import random


quiz_length = 20
# Grab species list
if not os.path.isfile("species.txt"):
    raise FileNotFoundError("no species.txt file found")
f = open("species.txt")
species_list = f.readlines()
for i in range(len(species_list)):
    species_list[i] = species_list[i][:-1]

# Figure out how many images of each species needs to be pulled
list_length = int(quiz_length / len(species_list))
length_dict = {}
for species in species_list:
    length_dict[species] = list_length
for species in random.sample(species_list, quiz_length % len(species_list)):
    length_dict[species] += 1

# Generate lists of indexes of images to pull
index_dict = {}
for species in length_dict:
    index_dict[species] = random.sample(range(1, 31), length_dict[species])

# Pull images from each species
# Open Browser
browser = webdriver.Chrome()
browser.minimize_window()
browser.get('https://media.ebird.org/catalog')
if not os.path.isdir("Quizzes"):
    os.mkdir("Quizzes")
time1 = datetime.datetime.now()
path = "Quizzes\\" + str(datetime.date.today()) + "-" + str(time1.hour) + "-" + str(time1.minute)
os.mkdir(path)
for species in index_dict:
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
    # Load 30 more images
    more_button = browser.find_element(by=By.XPATH,
                                       value='//*[@id="content"]/div/div/form/div[3]/button')
    more_button.click()
    # Locate the indexed photos and download them
    browser.implicitly_wait(5)
    for i in index_dict[species]:
        xpath = '//*[@id="content"]/div/div/form/ol/li[' + str(i) + ']/div[1]/div/img'
        img = browser.find_element(By.XPATH, xpath)
        src = img.get_attribute('src')
        # Create the file
        file_name = str(path + "\\" + species + str(i) + ".jpg")
        urllib.request.urlretrieve(src, file_name)
