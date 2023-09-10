import requests
import pandas as pd
import os

CHECKLIST_URL = "https://com-aab-media.s3.amazonaws.com/common/ebird_taxonomy_v2022.csv"
ABA_CHECKLIST_URL = "https://www.aba.org/wp-content/uploads/2020/03/ABA_Checklist-8.12.csv"
CHECKLIST_NAME = "ebird_taxonomy_v2022.csv"
ABA_CHECKLIST_NAME = "ABA_Checklist-8.12.csv"

class Validate():

    def __init__(self) -> None:
        """Gets the 2022 taxononmy, and initalizes the set"""
        # Verify/download eBird and ABA checklists
        if not os.path.isfile("BirdQuiz/resources/" + CHECKLIST_NAME):
            self.get_checklist_from_url()
        if not os.path.isfile("BirdQuiz/resources/" + ABA_CHECKLIST_NAME):
            self.get_checklist_from_url(aba=True)
        # Load the eBird checklist
        df = pd.read_csv("BirdQuiz/resources/" + CHECKLIST_NAME)
        self.species_set = set(df["PRIMARY_COM_NAME"])
        # Load the ABA checklist
        aba_header = ["blank", "Common Name", "Spanish", "Latin", "ABA Code", "Rarity Code"]
        df_ABA = pd.read_csv("BirdQuiz/resources/" + ABA_CHECKLIST_NAME, header=2, names=aba_header).dropna(axis=0, subset="Common Name")
        aba_code_dict = df_ABA.set_index("Common Name").to_dict()["ABA Code"]
        df["ABA_CODE"] = df.apply(lambda row: aba_code_dict.get(row["PRIMARY_COM_NAME"]), axis=1)
        # Create "words" dict
        words = {}
        for index, row in df.iterrows():
            words[row["PRIMARY_COM_NAME"]] = {}
        # Create a new column for synonyms
        df["SYNONYMNS"] = df.apply(self.list_synonyms, axis=1)
        synonyms = df.set_index("PRIMARY_COM_NAME").to_dict()["SYNONYMNS"]
        # Create autocomplete object
        self.ac = AutoComplete(words=words, synonyms=synonyms)


    def list_synonyms(self, row: pd.Series):
        l = []
        for header in ["SCI_NAME", "ABA_CODE"]:
            if row[header] is not None:
                l.append(row[header])
        return l

    def get_checklist_from_url(self, aba=False):
        """Downloads the 2022 eBird or ABA taxonomy list to resources"""
        if aba:
            name = ABA_CHECKLIST_NAME
            url = ABA_CHECKLIST_URL
        else:
            name = CHECKLIST_NAME
            url = CHECKLIST_URL
        with open(name, "wb") as f:
            f.write(requests.get(url).content)

    def validate(self, name: str):
        """Very basic set check"""
        return name in self.species_set

    def search(self, name: str):
        return self.ac.search(word=name, max_cost=3, size=5)

if __name__ == "__main__":
    v = Validate()
    print("\"Wood Thrush\" is valid: " + str(v.validate("Wood Thrush")))
    print("\"Aaron Sun\" is valid: " + str(v.validate("Aaron Sun")))
    prompt = input("Enter a Bird to search for (enter \"q\" to quit):\n")
    while prompt != "q":
        print("search results for \"" + prompt + "\": " + str(v.search(prompt)))
        prompt = input("Enter a Bird to search for (enter \"q\" to quit):\n")
