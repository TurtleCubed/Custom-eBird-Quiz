import http.client
import json
from json.decoder import JSONDecodeError
from calendar import monthrange
from random import randint

class BirdAPI:
	def __init__(self, region):
		self.conn = http.client.HTTPSConnection("api.ebird.org")
		self.payload = ''
		self.headers = {
			'X-eBirdApiToken': '6c8plv8d6h6b'
		}
		self.curr_checklist = None
		self.min_species = 20
		self.region = region

	def get_checklist(self):
		if self.curr_checklist is None:
			self.new_checklist()
		return self.curr_checklist["obsDt"] + " https://ebird.org/checklist/" + self.curr_checklist["subId"] + "\n" + self.specieslist(self.curr_checklist)

	def get_location(self):
		return self.hotspotloc(self.curr_checklist)

	def new_checklist(self):
		for _ in range(10):
			y = randint(2000, 2022)
			m = randint(1, 12)
			d = randint(1, monthrange(y, m)[1])
			self.curr_checklist = self.filterspecies(self.getchecklists(self.region, y, m, d), self.min_species)
			if self.curr_checklist:
				return
		# print(self.curr_checklist)
		print(f"Unable to find checklist in region {self.region} with species list of at least {self.min_species}!")
		assert self.curr_checklist

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

	def filterspecies(self, checklists, minspecies):
		for c in checklists:
			clist = self.lookup(f"/v2/product/checklist/view/{c['subID']}")
			if len(clist["obs"]) >= minspecies and self.lookup(f"/v2/ref/hotspot/info/{clist['locId']}"):
				return clist

	def specieslist(self, clist):
		out = ""
		for sp in clist["obs"]:
			out += str(sp["howManyStr"]) + " " + self.taxonomy(sp["speciesCode"]) + "\n"
			if "comment" in sp:
				out += "\t" + str(sp["comment"]) + "\n"
		return out

	def hotspotloc(self, checklist):
		hotspot = self.lookup(f"/v2/ref/hotspot/info/{checklist['locId']}")
		return hotspot["latitude"], hotspot["longitude"], hotspot["hierarchicalName"]

