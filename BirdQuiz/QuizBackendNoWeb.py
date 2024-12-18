import requests
from PIL import Image
from random import sample, randint
from threading import Thread, Event
import os, datetime
from QuizBackend import QuizBackend
from pathlib import Path
import csv
from io import BytesIO

# TODO: probabilistic sampling of species
# TODO: error handling

class QuizBackendNoWeb(QuizBackend):
    """
    QuizBackend Constantly runs fetch() in a separate thread to load bird images into memory.
    """
    def __init__(self):
        super().__init__(no_browser=True)
        # Get eBird codes and species names
        self.taxon = {}
        self.load_ebird_taxonomy()
        # self.open_browser()
        # self.cookies = self.browser.get_cookies()
        # self.browser.close()

    def fetch_until_stop(self):
        """Fetch images until we have the desired number of bird images."""
        while len(self.species) <= self.questions:
            self.fetch()
    
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
        '''Get a list of 30 URLs for a particular species from the URL search.'''
        imgurls = []
        while len(imgurls) == 0:
            # Set random month
            month = [i for i in range(1, 13) if ((i >= self.begin_month and i <= self.end_month) if self.begin_month <= self.end_month else not (i < self.begin_month and i > self.end_month))]
            month = month[randint(0, len(month) - 1)]
            year = randint(self.begin_year, self.end_year)
            print(month, year)
            url = f'https://media.ebird.org/api/v2/search?taxonCode={birdid}&sort=rating_rank_desc&mediaType=photo&birdOnly=true&beginMonth={month}&endMonth={month}&beginYear={year}&endYear={year}'
            out = requests.get(url, cookies={'ml-search-session': 'eyJ1c2VyIjp7InVzZXJJZCI6IlVTRVIxMDExNTE3IiwidXNlcm5hbWUiOiJhYXJvc3VuIiwiZmlyc3ROYW1lIjoiQWFyb24iLCJsYXN0TmFtZSI6IlN1biIsImZ1bGxOYW1lIjoiQWFyb24gU3VuIiwicm9sZXMiOlsiYXVkaW8tYW5ub3RhdG9yIiwiY2hlY2tsaXN0LW1lZGlhLWJldGEtdGVzdGVyIl0sInByZWZzIjp7IlBST0ZJTEVfVklTSVRTX09QVF9JTiI6InRydWUiLCJQUklWQUNZX1BPTElDWV9BQ0NFUFRFRCI6InRydWUiLCJQUk9GSUxFX09QVF9JTiI6InRydWUiLCJTSE9XX1NVQlNQRUNJRVMiOiJ0cnVlIiwiRElTUExBWV9OQU1FX1BSRUYiOiJuIiwiVklTSVRTX09QVF9PVVQiOiJmYWxzZSIsIkRJU1BMQVlfQ09NTU9OX05BTUUiOiJ0cnVlIiwiRElTUExBWV9TQ0lFTlRJRklDX05BTUUiOiJmYWxzZSIsIlBST0ZJTEVfUkVHSU9OIjoiVVMiLCJTSE9XX0NPTU1FTlRTIjoidHJ1ZSIsIlJFR0lPTl9QUkVGIjoid29ybGQiLCJDT01NT05fTkFNRV9MT0NBTEUiOiJlbl9VUyIsIkdNQVBfVFlQRSI6InJvYWRtYXAiLCJBTEVSVFNfT1BUX09VVCI6ImZhbHNlIiwiRU1BSUxfQ1MiOiJmYWxzZSIsIkxJU1RfRElTUExBWSI6ImFsbENvdW50aWVzIiwiVE9QMTAwX09QVF9PVVQiOiJmYWxzZSIsIlNPUlRfVEFYT04iOiJ0cnVlIiwic3BwUHJlZiI6ImNvbW1vbiJ9fX0=', 'ml-search-session.sig': 'nDcDcTxZsl0fVfCWxlCdWbHPekw'})
            # out = requests.get(url, cookies=self.cookies)
            out = [x['assetId'] for x in out.json()]
            imgurls = [f'https://cdn.download.ams.birds.cornell.edu/api/v1/asset/{i}/' for i in out]
        return imgurls

    def load_ebird_taxonomy(self, path=Path("resources", "ebird_taxonomy_v2024.csv")):
        '''Load a dictonary copy of the eBird Taxonomy. The url search uses bird ID instead of species name'''
        with open(path, 'r') as f:
            taxon = csv.reader(f)
            for l in taxon:
                self.taxon[l[4]] = l[2]
