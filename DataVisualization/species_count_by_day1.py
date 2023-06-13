import os
import json
from datetime import datetime
import pandas as pd
import matplotlib.pyplot as plt

data_path = 'DataVisualization\\Data\\US_Stats.json'


dates = []
species_count = []
checklist_count = []
contributor_count = []

f = open(data_path)
loaded_json = json.load(f)
f.close()

for d in loaded_json:
    dates.append(datetime.strptime(d, "%Y_%m_%d"))
    species_count.append(int(loaded_json[d]["numSpecies"]))
    checklist_count.append(int(loaded_json[d]["numChecklists"]))
    contributor_count.append(int(loaded_json[d]["numContributors"]))


fig, ax1 = plt.subplots()
fig.suptitle('United States')
ax1.set_ylabel('Number of Checklists and Contributors')
ax1.set_xlabel('Date')
ax1.plot(dates, checklist_count, 'b-', label="Checklists")
ax1.plot( dates, contributor_count, 'g-', label="Contributors")
ax1.legend(loc="upper left")
ax2 = ax1.twinx()
ax2.set_ylabel('Number of Species')
ax2.plot(dates, species_count, 'r-', label="Species")
ax2.legend(loc="upper right")
plt.gcf().autofmt_xdate()
plt.show()

