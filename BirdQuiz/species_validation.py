import requests
import pandas as pd
import os

CHECKLIST_URL = "https://com-aab-media.s3.amazonaws.com/common/ebird_taxonomy_v2022.csv"
CHECKLIST_NAME = "ebird_taxonomy_v2022.csv"

class Validate():

    def __init__(self) -> None:
        """Gets the 2022 taxononmy, and initalizes the validation set"""
        if not os.path.isfile("BirdQuiz/resources/" + CHECKLIST_NAME):
            self.get_checklist_from_url()
        df = pd.read_csv("BirdQuiz/resources/" + CHECKLIST_NAME)
        self.species_set = set(df["PRIMARY_COM_NAME"])

    def get_checklist_from_url(self):
        """Downloads the 2022 eBird taxonomy list to resources"""
        with open(CHECKLIST_NAME, "wb") as f:
            f.write(requests.get(CHECKLIST_URL).content)

    def validate(self, name: str):
        """Very basic set check"""
        return name in self.species_set



if __name__ == "__main__":
    v = Validate()
    print("\"Wood Thrush\" is valid: " + str(v.validate("Wood Thrush")))
    print("\"Aaron Sun\" is valid: " + str(v.validate("Aaron Sun")))
