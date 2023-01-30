import http.client
import json
from json.decoder import JSONDecodeError
from calendar import monthrange
from random import randint
from threading import Thread

class BirdAPI:
	def __init__(self, region, n):
		self.conn = http.client.HTTPSConnection("api.ebird.org")
		self.payload = ''
		self.headers = {
			'X-eBirdApiToken': '6c8plv8d6h6b'
		}
		self.load_total = n
		self.i = 0
		self.checklists = []
		self.locs = []
		self.tax = {}
		self.curr_checklist = None
		self.min_species = 20
		self.region = region
		self.begin_thread()

	def begin_thread(self):
		"""Begin a new thread that fetches until we have the desired number of checklists"""
		Thread(target=self.fetch_until_stop).start()

	def fetch_until_stop(self):
		"""Fetch checklists until we have the desired number."""
		n_fail = 0
		while n_fail < 10 and len(self.checklists) < self.load_total:
			y = randint(2000, 2022)
			m = randint(1, 12)
			d = randint(1, monthrange(y, m)[1])
			checklists = self.getchecklists(self.region, y, m, d)
			for c in checklists:
				clist = self.lookup(f"/v2/product/checklist/view/{c['subID']}")
				if len(clist["obs"]) >= self.min_species and self.percent_X(clist["obs"]) < 0.5:
					if clist not in self.checklists and self.process_checklist(clist):
						self.checklists.append(clist)
				if len(self.checklists) == self.load_total:
					break
			n_fail += 1
		if n_fail >= 10:
			print(f"Unable to find checklist in region {self.region} with species list of at least {self.min_species}!")
			assert n_fail < 10

	def percent_X(self, obs):
		X = 0
		for sp in obs:
			if str(sp["howManyStr"]) == "X":
				X += 1
		return X / len(obs)

	def process_checklist(self, checklist):
		self.locs.append(self.hotspotloc(checklist))
		if self.locs[-1] is None:
			self.locs.pop()
			return False
		for sp in checklist["obs"]:
			if sp["speciesCode"] not in self.tax:
				self.tax[sp["speciesCode"]] = self.taxonomy(sp["speciesCode"])
		return True

	def get_checklist(self):
		if len(self.checklists) <= self.i:
			print("Loading checklist... please wait.")
		while len(self.checklists) <= self.i:
			pass
		curr_checklist = self.checklists[self.i]
		return curr_checklist["obsDt"] + " https://ebird.org/checklist/" + curr_checklist["subId"] + "\n" + self.specieslist(curr_checklist)

	def get_location(self):
		self.i += 1
		return self.locs[self.i-1]

	# def new_checklist(self):
	# 	for _ in range(10):
	# 		y = randint(2000, 2022)
	# 		m = randint(1, 12)
	# 		d = randint(1, monthrange(y, m)[1])
	# 		self.curr_checklist = self.filterspecies(self.getchecklists(self.region, y, m, d), self.min_species)
	# 		print(self.curr_checklist)
	# 		if self.curr_checklist:
	# 			return
	# 	# print(self.curr_checklist)
	# 	print(f"Unable to find checklist in region {self.region} with species list of at least {self.min_species}!")
	# 	assert self.curr_checklist

	# Below are lookup tools

	def lookup(self, url):
		try:
			self.conn.request("GET", url, self.payload, self.headers)
			res = self.conn.getresponse()
		except http.client.RemoteDisconnected:
			self.conn = http.client.HTTPSConnection("api.ebird.org")
			return self.lookup(url)
		data = res.read()
		try:
			return json.loads(data.decode('utf-8'))
		except JSONDecodeError:
			return data.decode('utf-8')

	def taxonomy(self, spcode):
		return self.lookup(f"/v2/ref/taxonomy/ebird?species={spcode}").split(",")[15]

	def getchecklists(self, region, y, m, d):
		query = f"/v2/product/lists/{region}/{y}/{m}/{d}?maxResults=200"
		return self.lookup(query)

	def specieslist(self, clist):
		out = ""
		for sp in clist["obs"]:
			out += str(sp["howManyStr"]) + " " + self.tax[sp["speciesCode"]]
			if "comments" in sp:
				out += ": " + str(sp["comments"]) + "\n"
			else:
				out += "\n"
		return out

	def hotspotloc(self, checklist):
		hotspot = self.lookup(f"/v2/ref/hotspot/info/{checklist['locId']}")
		if not hotspot:
			return None
		return hotspot["latitude"], hotspot["longitude"], hotspot["hierarchicalName"]
