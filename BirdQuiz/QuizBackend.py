from selenium import webdriver
from selenium.webdriver.chrome.service import Service
import requests
from PIL import Image
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from random import sample, randint
from threading import Thread, Event
import os, datetime

# TODO: probabilistic sampling of species
# TODO: change species name navigation to use URL search

class QuizBackend():
    """
    QuizBackend Constantly runs fetch() in a separate thread to load bird images into memory.
    """
    def __init__(self, questions=20, download=False, from_file=False):
        super().__init__()
        self.event = Event()

        # Sort species
        self.alpha_species = sorted(set([x[:-1].strip() for x in open("species.txt", "r").readlines() if x[:-1].strip()]))
        self.species = []
        self.imgs = []
        self.guesses = []

        # Set other parameters
        self.download = download
        self.from_file = from_file
        self.questions = questions
        self.i = 0
        self.correct = 0

        self.browser_thread = Thread(target=self.open_browser)
        self.browser_thread.start()

        
        self.transform = lambda x: x

    def add_black_white(self):
        """Add a black and white transformation"""
        self.transform = lambda im: im.convert('L')

    def open_browser(self):
        """Open the browser in headless mode and navigate to Macaulay library"""
        if not self.from_file:
            # Open Browser and set parameters
            service = Service()
            chrome_options = self.get_headless_options()
            # self.browser = webdriver.Chrome(ChromeDriverManager(cache_manager=DriverCacheManager(root_dir="./resources")).install(), options=chrome_options)
            self.browser = webdriver.Chrome(service=service, options=chrome_options)
            self.browser.minimize_window()
            self.browser.get('https://media.ebird.org/catalog?view=grid&mediaType=photo')
            self.search_box = self.browser.find_element(by=By.ID, value="taxonFinder")

    def get_headless_options(self):
        """Returns an options object with special configurations for headless running."""
        chrome_options = Options()
        # This line hides the browser
        user_agent = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.50 Safari/537.36'
        chrome_options.add_argument(f'user-agent={user_agent}')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--allow-running-insecure-content')
        chrome_options.add_argument("--headless")
        chrome_options.add_argument('log-level=2')
        return chrome_options

    def get_current(self):
        """Return the image for the current species to guess."""
        while self.i + 1 >= len(self.imgs): # Wait for fetch to get the correct image
            pass
        return self.transform(self.imgs[self.i])

    def get_species(self):
        """Get the current species name."""
        return self.species[self.i]
    
    def check(self, answer):
        """Check whether the answer matches the current species."""
        self.guesses.append(answer)
        correct = self.species[self.i] == answer
        if correct:
            self.correct += 1
        return correct

    def next_species(self):
        """Go to the next species."""
        self.i += 1

    def begin_thread(self):
        """Begin a new thread that fetches until we have the desired number of images"""
        Thread(target=self.fetch_until_stop).start()

    def fetch_until_stop(self):
        """Fetch images until we have the desired number of bird images."""
        while self.browser_thread.is_alive(): # While the browser is not yet open
            pass
        while len(self.species) <= self.questions:
            self.fetch()
        if not self.from_file:
            # When we're done, close the browser
            self.browser.close()
    
    def fetch(self):
        """Choose the next species and fetch an image for that species."""
        self.species.append(sample(self.alpha_species, 1)[0])
        if self.from_file:
            self.imgs.append(self.get_image_from_file(self.species[-1]))
        else:
            self.imgs.append(self.get_image(self.species[-1]))
        if self.download and not self.from_file:
            if not os.path.isdir(f"./Quizzes/{self.species[-1]}"):
                os.mkdir(f"./Quizzes/{self.species[-1]}")
            self.imgs[-1].convert('RGB').save(f"./Quizzes/{self.species[-1]}/{datetime.datetime.now().timestamp()}.jpg")

    def get_image_from_file(self, species_name, num_imgs=1):
        root = f"./Quizzes/{species_name}"
        fnames = sample(os.listdir(root), num_imgs)
        imgs = []
        for fname in fnames:
            imgs.append(Image.open(root + "/" + fname))
        return imgs[0] if num_imgs == 1 else imgs

    def get_image(self, species_name, num_imgs=1):
        """Get a bird image for a particular species"""
        self.search_bird(species_name)
        return self.load_imgs(num_imgs)

    def search_bird(self, species_name):
        """Search the species in the browser"""
        # Clear search bar
        self.clear_search()
        self.search_box.clear()
        # Set random month
        month = randint(1, 12)
        # year = randint(2015, 2023)
        self.browser.get(f'https://media.ebird.org/catalog?view=grid&mediaType=photo&beginMonth={month}&sort=rating_rank_desc')
        self.search_box = self.browser.find_element(by=By.ID, value="taxonFinder")
        # Type species name, then wait for autofill suggestion
        self.search_box.send_keys(species_name)
        while len(self.browser.find_elements(by=By.ID, value="Suggest-suggestion-0")) == 0:
            pass
        suggestion0 = self.browser.find_element(by=By.ID, value="Suggest-suggestion-0")
        suggestion0.click()
        # Hit load more, then wait for the images to load
        while len(self.browser.find_elements(by=By.CSS_SELECTOR, value='[class="Button u-margin-none"]')) == 0:
            pass
        more_button = self.browser.find_element(by=By.CSS_SELECTOR, value='[class="Button u-margin-none"]')
        more_button.click()
        while len(self.browser.find_elements(By.CSS_SELECTOR, value='[class="ResultsGrid-card-image"]')) == 0:
            pass

    def clear_search(self):
        """Clear the search bar by hitting the x button"""
        try:
            self.browser.find_element(by=By.CLASS_NAME, value="Suggest-reset").click()
        except NoSuchElementException:
            pass

    def load_imgs(self, num_imgs=1):
        """Download NUM_IMGS from searched images into memory"""
        imgs = []
        # These are <div> objects with images inside
        divs = self.browser.find_elements(By.CSS_SELECTOR, value='[class="ResultsGrid-card-image"]')
        assert len(divs) > 0
        # Sampling randomly from this list
        for i in sample(range(len(divs)), num_imgs):
            # Read image into memory via some annoying means
            element = divs[i].find_elements(By.TAG_NAME, "img")[0]
            request = requests.get(element.get_attribute('src'), stream=True)
            img = Image.open(request.raw)#np.array(Image.open(request.raw))
            imgs.append(img)
        return img if num_imgs == 1 else imgs
