import os
import json
from datetime import datetime
import pandas as pd
import matplotlib.pyplot as plt

data_path = 'DataVisualization\\Data'
dir_list = os.listdir(data_path)


dates = []
species_count = []
checklist_count = []

for fn in dir_list:
    f = open(os.path.join(data_path, fn), encoding='utf8')
    loaded_json = json.load(f)
    f.close()

    date = datetime.strptime(fn[-10:], "%Y_%m_%d")

    if fn.startswith('species_'):
        species_count.append(len(loaded_json))
    if fn.startswith('checklists_'):
        dates.append(date)
        checklist_count.append(len(loaded_json))

plt.plot(dates, species_count, 'r-', dates, checklist_count, 'b-')
plt.gcf().autofmt_xdate()
plt.show()

