from selenium import webdriver
from selenium.webdriver.support.wait import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager
from time import sleep

driver = webdriver.Chrome(ChromeDriverManager(path="./BirdQuiz/resources").install())
driver.get("https://www.google.com/maps/@40.094099,-98.3882497,4z")

def wait_click_pin(driver, timeout=300):
    wait = WebDriverWait(driver, timeout)
    wait.until(lambda driver: driver.current_url.startswith("https://www.google.com/maps/place/"))
    s = driver.current_url.split("@", 1)[1].split(",")
    return [float(s[0]), float(s[1])]

def show_true(driver, guess, actual):
    driver.get(f"https://www.google.com/maps/dir/'{guess[0]},{guess[1]}'/'{actual[0]},{actual[1]}'")
exit()
