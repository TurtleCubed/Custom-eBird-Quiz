from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
import requests
from PIL import Image
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from random import sample, randint
from threading import Thread, Event

# TODO: probabilistic sampling of species
# TODO: change species name navigation to use URL search

class QuizBackend():
    """
    QuizBackend Constantly runs fetch() in a separate thread to load bird images into memory.
    """
    def __init__(self, questions=20):
        super().__init__()
        self.event = Event()
        # Open Browser and set parameters
        self.browser = webdriver.Chrome(ChromeDriverManager(path="./resources").install())
        self.browser.minimize_window()
        self.browser.get('https://media.ebird.org/catalog?view=grid&mediaType=photo')
        self.search_box = self.browser.find_element(by=By.ID, value="taxonFinder")

        # Sort species
        self.alpha_species = sorted([x[:-1].strip() for x in open("species.txt", "r").readlines() if x[:-1].strip()])
        self.species = []
        self.imgs = []
        self.guesses = []

        # Set other parameters
        self.questions = questions
        self.i = 0
        self.correct = 0
        self.begin_thread()

    def get_current(self):
        """Return the image for the current species to guess."""
        while self.i + 1 >= len(self.imgs): # Wait for fetch to get the correct image
            pass
        return self.imgs[self.i]

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
        while len(self.species) <= self.questions:
            self.fetch()
        # When we're done, close the browser
        self.browser.close()
    
    def fetch(self):
        """Choose the next species and fetch an image for that species."""
        self.species.append(sample(self.alpha_species, 1)[0])
        self.imgs.append(self.get_image(self.species[-1]))

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
        self.browser.get(f'https://media.ebird.org/catalog?view=grid&mediaType=photo&beginMonth={month}')
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
