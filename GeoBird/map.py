from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from time import sleep

driver = webdriver.Chrome(ChromeDriverManager(path="./BirdQuiz/resources").install())
driver.get("https://www.google.com/maps/@40.094099,-98.3882497,4z")


