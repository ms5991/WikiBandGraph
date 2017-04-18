#!/bin/python
from bs4 import BeautifulSoup

import requests
import json

class Act(object):
	
	WikipediaRoot = 'https://en.wikipedia.org'

	def __init__(self, name, link, associatedActs):
		self.name = name
		self.link = link
		self.associatedActs = associatedActs

			

def persist(currentAct, filename):
	with open(filename, 'a') as outfile:
		json.dump(currentAct.__dict__, outfile)
		outfile.write('\n')
		

def getSingleAct(url, name):
	r  = requests.get(url)

	data = r.text

	soup = BeautifulSoup(data, "html5lib")

	table = soup.find('table', attrs={'class':'infobox'})

	if table is None:
		return Act(name, {})

	table_body = table.find('tbody')

	rows = table_body.find_all('tr')
	associatedActs = {}
	
	for row in rows:
		headers = row.find_all('th')	   

		for head in headers:

			if head.text.lower() == 'Associated Acts'.lower():

				data = row.find_all('td')

				for act in data:
					links = act.find_all('a')
					
					for link in links:
						associatedActs[link.get('title')] = link.get('href')
	
				break
	return Act(name, associatedActs)

def crawl(rootAct, filename):

	visited = set()
	stack = [rootAct]

	visited.add(rootAct.name)

	while stack:
		vertex = stack.pop()

		print('Popped: ' + vertex.name)
		persist(vertex, filename)
		
		for associatedAct in vertex.associatedActs:
			if associatedAct not in visited:
				print('Adding to stack: ' + associatedAct) 
				assAct = getSingleAct(Act.WikipediaRoot + vertex.associatedActs[associatedAct], associatedAct)
				stack.append(assAct)
				visited.add(associatedAct)
	
				
def main():
	url = raw_input("Enter a Wikipedia URL to start from (form: '/wiki/BAND_ARTICLE': ")

	print(url)

	filename = 'output.json'

	
	root = getSingleAct(Act.WikipediaRoot + url, url)
	persist(root, filename)

	crawl(root, filename)


if  __name__ =='__main__':main()

