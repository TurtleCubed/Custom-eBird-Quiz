import requests
from PIL import Image
from random import sample, randint
from threading import Thread, Event
import os, datetime
from pathlib import Path
import csv
from io import BytesIO

# TODO: probabilistic sampling of species

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

        # Get eBird codes and species names
        self.taxon = {}
        self.load_ebird_taxonomy()
        
        self.transform = lambda x: x

    def add_black_white(self):
        """Add a black and white transformation"""
        self.transform = lambda im: im.convert('L')

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
        while len(self.species) <= self.questions:
            self.fetch()
    
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
        return self.load_imgs(species_name, num_imgs)

    def load_imgs(self, species_name, num_imgs=1):
        """Download NUM_IMGS from searched images into memory"""
        imgs = []
        urls = self.get_urls(self.taxon[species_name])

        # Sampling randomly from this list
        for url in sample(urls, num_imgs):
            # Read image into memory
            request = requests.get(url)
            img = Image.open(BytesIO(request.content))#np.array(Image.open(request.raw))
            imgs.append(img)
        return img if num_imgs == 1 else imgs
    
    def get_urls(self, birdid):
        '''Skip the web browser and use the URL search'''
        # Set random month
        month = randint(1, 12)
        url = f'https://media.ebird.org/api/v2/search?taxonCode={birdid}&sort=rating_rank_desc&mediaType=photo&birdOnly=true&beginMonth={month}'
        out = requests.get(url, cookies={'ml-search-session': 'eyJ1c2VyIjp7ImFub255bW91cyI6dHJ1ZX19', 'ml-search-session.sig': 'XZPO3pJ50PRL94J3OagC3Bg1IVk'})
        out = [x['assetId'] for x in out.json()]
        imgurls = [f'https://cdn.download.ams.birds.cornell.edu/api/v1/asset/{i}/' for i in out]
        return imgurls

    def load_ebird_taxonomy(self, path=Path("resources", "ebird_taxonomy_v2022.csv")):
        '''Load a dictonary copy of the eBird Taxonomy. The url search uses bird ID instead of species name
        TODO: download the taxonomy if it does not already exist'''
        with open(path, 'r') as f:
            taxon = csv.reader(f)
            for l in taxon:
                self.taxon[l[3]] = l[2]
