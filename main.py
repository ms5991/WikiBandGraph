#!/bin/python
from bs4 import BeautifulSoup

#imports
import requests
import json
import networkx as nx
import time

class Act(object):
	
	WikipediaRoot = 'http://192.168.113.11:8080'

	def __init__(self, name, link, associatedActs):
		self.name = name
		self.link = link
		self.associatedActs = associatedActs

def getSingleAct(actSub):

	try:
		r  = requests.get(Act.WikipediaRoot + actSub)
	except KeyboardInterrupt:
		raise
	except e:
		try:
			print('ERROR:\t\t' + str(e.message))
		except:
			print('ERROR:\t\t cannot print original error message')
		return None

	data = r.text

	actSub = r.url[len(Act.WikipediaRoot):]

	soup = BeautifulSoup(data, "html5lib")

	table = soup.find('table', attrs={'class':'infobox'})

	titleheader = soup.find('h1', attrs={'id':'firstHeading'})

	if table is None:
		print('Unable to find table for:\t' + actSub)
		return Act(titleheader.text, actSub, {})

	table_body = table.find('tbody')

	if table_body is None:
		print('Unable to find table body for:\t' + actSub)
		return Act(titleheader.text, actSub, {})

	rows = table_body.find_all('tr')

	if rows is None:
		print('Unable to find rows for:\t' + actSub)
		return Act(titleheader.text, actSub, {})


	associatedActs = {}

	for row in rows:
		headers = row.find_all('th')	   

		for head in headers:

			if head.text.lower().strip(' \t\n\r') == 'Associated Acts'.lower():

				data = row.find_all('td')
				for act in data:
					links = act.find_all('a')

					
					for link in links:
						associatedActs[link.get('title')] = link.get('href')
	
				break

	return Act(titleheader.text, actSub, associatedActs)

def buildAndOutputGraph(rootAct, filename, countLimit):

	visited = set()
	stack = [rootAct]

	visited.add(rootAct.name)

	G = nx.Graph()
	G.add_node(rootAct.name, link = Act.WikipediaRoot + rootAct.link)

	redirectCache = {}
	count = 0
	while stack and count < countLimit:
		vertex = stack.pop()
		print('Popped to explore:\t' + vertex.name.encode('unicode-escape') + '\tat count: ' + str(count))

		count += 1		

		# write a backup file every 256 expansions
		if(count % 256 == 0 and count != 0):
			print('Writing backup file and sleeping...')
			nx.write_gexf(G, 'backup_' + str(count) + '.gexf')
			time.sleep(10)

		for associatedAct in vertex.associatedActs:
			if associatedAct not in visited:
				#build the Act object for this band
				assAct = getSingleAct(vertex.associatedActs[associatedAct])

				if assAct is None:
					print('Trying to continue loop')
					visited.add(associatedAct)
					G.add_edge(vertex.name, associatedAct)
					time.sleep(10)
					continue
				
				print('Adding NODE:\t' + assAct.name.encode('unicode-escape')) 

				#add to stack to explore later
				stack.append(assAct)
				
				#check to see if there was a redirect
				#if so, add to cache and add the redirected name as well
				if associatedAct != assAct.name:
					redirectCache[associatedAct] = assAct.name
					visited.add(assAct.name)

				#add this to visited so we don't generate another one
				visited.add(associatedAct)
	
				#add node to graph
				G.add_node(assAct.name, link = Act.WikipediaRoot + assAct.link)	

			#check if the band has a redirected name (aka get the name from the band's page, not the url from the incoming link)
			toAdd = associatedAct
			if associatedAct in redirectCache:
				toAdd = redirectCache[associatedAct]

			#add the edge
			print('Adding EDGE from:\t' + vertex.name.encode('unicode-escape') + ' to: ' + toAdd.encode('unicode-escape'))
			G.add_edge(vertex.name, toAdd)
	print('Done building graph')

	nx.write_gexf(G, filename)
	
				
def main():
	url = raw_input("Enter a Wikipedia URL to start from (form: '/wiki/BAND_ARTICLE': ")

	print(url)


	filename = 'output.gexf'

	
	root = getSingleAct(url)

	while root is None:
		time.sleep(1.2)
		root = getSingleAct(url)
		print('Retrying to get root')

	buildAndOutputGraph(root, filename, 1000000)


if  __name__ =='__main__':main()

