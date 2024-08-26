from selenium import webdriver
from selenium.webdriver.support.wait import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.core.driver_cache import DriverCacheManager
from selenium.webdriver.chrome.options import Options
from math import sin, cos, sqrt, atan2, radians

class GMap:
    def __init__(self, view="40.094099,-98.3882497,4z"):
        chrome_options = Options()
        chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
        self.driver = webdriver.Chrome(ChromeDriverManager(cache_manager=DriverCacheManager(root_dir="./resources")).install(), options=chrome_options)
        self.view = view
        self.reset()

    def reset(self):
        self.driver.get(f"https://www.google.com/maps/@{self.view}")

    def wait_click_pin(self, timeout=300):
        wait = WebDriverWait(self.driver, timeout)
        wait.until(lambda driver: "17z" in driver.current_url or "15z" in driver.current_url)
        s = self.driver.current_url.split("/@", 1)[1].split(",17z")[0]
        s = s.split(",")
        # print(s)
        return [float(s[0]), float(s[1])]

    def show_true(self, guess, actual):
        self.driver.get(f"https://www.google.com/maps/dir/'{guess[0]},{guess[1]}'/'{actual[0]},{actual[1]}'")

    def close(self):
        self.driver.close()
    
    def distance(self, guess, actual, miles=False):
        # approximate radius of earth in km
        R = 6373.0

        lon1, lat1 = map(radians, guess)
        lon2, lat2 = map(radians, actual)

        dlon = lon2 - lon1
        dlat = lat2 - lat1

        a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
        c = 2 * atan2(sqrt(a), sqrt(1 - a))

        distance = R * c
        # print(guess, actual, distance)
        if miles:
            return distance * 0.621371
        return distance