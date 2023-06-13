import requests
from datetime import datetime, date, timedelta
import json
from tqdm import tqdm

API_TOKEN = '6c8plv8d6h6b'

def fetch_species_by_date(region_code, date):
  year = str(date.year)
  month = str(date.month).zfill(2)
  day = str(date.day).zfill(2)

  url = "https://api.ebird.org/v2/data/obs/{}/historic/{}/{}/{}".format(region_code, year, month, day)
  file_name = "DataVisualization\\Data\\species_{}_{}_{}_{}".format(region_code, year, month, day)

  payload={}
  headers = {
    'X-eBirdApiToken': API_TOKEN
  }

  response = requests.request("GET", url, headers=headers, data=payload)

  file = open(file_name, 'w', encoding="utf-8")
  file.write(response.text)
  file.close()

def fetch_checklists_by_date(region_code, date):
  year = str(date.year)
  month = str(date.month).zfill(2)
  day = str(date.day).zfill(2)

  url = "https://api.ebird.org/v2/product/lists/{}/{}/{}/{}".format(region_code, year, month, day)
  file_name = "DataVisualization\\Data\\checklists_{}_{}_{}_{}".format(region_code, year, month, day)

  payload={
    'maxResults': '200'
  }
  headers = {
    'X-eBirdApiToken': API_TOKEN
  }

  response = requests.request("GET", url, headers=headers, params=payload)

  file = open(file_name, 'w', encoding="utf-8")
  file.write(response.text)
  file.close()

def fetch_regional_statistics_by_date(region_code, date):
  year = str(date.year)
  month = str(date.month).zfill(2)
  day = str(date.day).zfill(2)

  url = "https://api.ebird.org/v2/product/stats/{}/{}/{}/{}".format(region_code, year, month, day)
  # file_name = "DataVisualization\\Data\\regional_statistics_{}_{}_{}_{}".format(region_code, year, month, day)

  payload={}
  headers = {
    'X-eBirdApiToken': API_TOKEN
  }

  response = requests.request("GET", url, headers=headers, data=payload)

  return response.text


start_date = date(2021, 1, 1)
end_date = date(2022, 1, 1)
date_list = []
delta = timedelta(days=1)
while (start_date < end_date):
    date_list.append(start_date)
    start_date += delta

r = 'US'
stats_string = "{"
for d in tqdm(date_list):
  date_string = str(d.year) + "_" + str(d.month).zfill(2) + "_" + str(d.day).zfill(2)
  stats_string += "\"" + date_string + "\":" + fetch_regional_statistics_by_date(r, d) + ","
stats_string = stats_string[:-1] + "}"

file_name = "DataVisualization\\Data\\US_Stats.json"

file = open(file_name, 'w', encoding="utf-8")
file.write(stats_string)
file.close()