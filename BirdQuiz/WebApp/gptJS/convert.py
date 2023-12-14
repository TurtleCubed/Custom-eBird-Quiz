import csv
import json

def csv_to_json(csv_file, json_file):
    data = []
    with open(csv_file, 'r') as file:
        csv_reader = csv.DictReader(file)
        for row in csv_reader:
            data.append(row)

    with open(json_file, 'w') as file:
        json.dump(data, file, indent=4)

# Replace 'input.csv' with your CSV file name and 'output.json' with the desired JSON file name
csv_to_json('ebird_taxonomy_v2023 (1).csv', 'ebird_taxonomy_v2023.json')
