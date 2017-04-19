#!/bin/python
from bs4 import BeautifulSoup

#imports
import requests
import json
import networkx as nx
import time
import sys
import pickle

class Act(object):
	
	# WikipediaRoot = 'http://192.168.113.11:8080'

	def __init__(self, name, link, associatedActs):
		self.name = name
		self.link = link
		self.associatedActs = associatedActs

def getSingleAct(wikipediaRoot, actSub):

	try:
		r  = requests.get(wikipediaRoot + actSub)
	except KeyboardInterrupt:
		raise
	except Exception, e:
		try:
			print('ERROR:\t\t' + str(e.message))
		except:
			print('ERROR:\t\t cannot print original error message')
		return None

	data = r.text

	actSub = r.url[len(wikipediaRoot):]

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

def loadVisitedSet():
	visited = None
	with open('visitedSet.dat', 'r') as v:
		visited = pickle.load(v)
	return visited

# loads a serialized stack
def loadStack():
	stack = None
	with open('stack.dat', 'r') as v:
		stack = pickle.load(v)
	return stack

# loads a serialized graph	
def loadGraph()
	return nx.read_gexf('graph.dat')

# loads a serialized count
def loadCount()
	count = None
	with open('count.dat', 'r') as v:
		count = pickle.load(v)
	return count

# loads a serialized cache
def loadRedirectCache()
	redirectCache = None
	with open('redirectCache.dat', 'r') as v:
		redirectCache = pickle.load(v)
	return redirectCache

# serializes the state of the dfs search
def writeState(graph, visited, stack, count, redirect):
	with open('visitedSet.dat', 'w') as v:
		pickle.dump(visited, v)

	with open('stack.dat', 'w') as v:
		pickle.dump(stack, v)

	nx.write_gexf(graph, 'graph.dat')

	with open('count.dat', 'w') as v:
		pickle.dump(count, v)

	with open('redirectCache.dat', 'w') as v:
		pickle.dump(redirect, v)
	


def buildAndOutputGraph(rootAct, wikipediaRoot, filename, countLimit, backupResolution, loadFromFiles = False):

	if loadFromFiles is False:
		
		# set of visited names
		visited = set()

		# list (stack) for dfs
		stack = [rootAct]

		#add the root node to visited
		visited.add(rootAct.name)

		# create graph
		G = nx.Graph()

		# add root node to graph
		G.add_node(rootAct.name, link = wikipediaRoot + rootAct.link)

		# for the case where a link to a page results in a redirect with a different name
		redirectCache = {}
		count = 0

	else:
		visited = loadVisitedSet()
		stack = loadStack()
		G = loadGraph()
		count = loadCount()
		redirectCache = loadRedirectCache()

	# while the stack has stuff in it
	while len(stack) > 0 and count < countLimit:
		
		# write a backup file at some number of expansions
		if(count % backupResolution == 0 and count != 0):
			print('Writing backup file...')
			nx.write_gexf(G, 'backup_' + str(count) + '.gexf')
			writeState(G, visited, stack, count, redirectCache)
			print('Wrote backup file!')

		# pop node to examime	
		currentNode = stack.pop()
		print('Popped to explore:\t' + currentNode.name.encode('unicode-escape') + '\tat count: ' + str(count))

		count += 1

		# for each outgoing link in this node's html
		for associatedAct in currentNode.associatedActs:

			# if we haven't already visted, we have to build a node
			if associatedAct not in visited:
				#build the Act object for this band
				assAct = getSingleAct(currentNode.associatedActs[associatedAct])

				# if None, probably had request exception.  Add edge and continue loop
				if assAct is None:
					print('Got None for: ' + associatedAct)
					visited.add(associatedAct)
					G.add_edge(currentNode.name, associatedAct)
					print('Adding EDGE from:\t' + currentNode.name.encode('unicode-escape') + ' to: ' + toAdd.encode('unicode-escape'))
					continue
				
				print('Adding NODE:\t\t' + assAct.name.encode('unicode-escape')) 

				#add node to stack to explore later
				stack.append(assAct)
				
				#check to see if there was a redirect
				#if so, add to cache and add the redirected name as well
				if associatedAct != assAct.name:
					redirectCache[associatedAct] = assAct.name
					visited.add(assAct.name)

				#add this to visited so we don't generate another one
				visited.add(associatedAct)
	
				#add node to graph
				G.add_node(assAct.name, link = wikipediaRoot + assAct.link)	

			#check if the band has a redirected name (aka get the name from the band's page, not the url from the incoming link)
			toAdd = associatedAct
			if associatedAct in redirectCache:
				toAdd = redirectCache[associatedAct]

			#always add the edge
			print('Adding EDGE from:\t' + currentNode.name.encode('unicode-escape') + ' to: ' + toAdd.encode('unicode-escape'))
			G.add_edge(currentNode.name, toAdd)

	print('Done building graph. Writing final file at: ' + filename)
	nx.write_gexf(G, filename)
	print('Finished writing file!')	
				
def main():

	# check args
	if len(sys.argv) != 5:
		print('error: usage is: python main.py [wikipedia-url-root] [output-file-name] [exploration-limit (-1 for no limit)] [backup-resolution]')
		sys.exit(-1)

	# parse args
	wikipediaRoot = sys.argv[1]
	outputFileName = sys.argv[2]
	countLimit = int(sys.argv[3])
	backupResolution = int(sys.argv[4])

	# infinite count
	if countLimit < 0:
		countLimit = sys.maxint

	# get input
	url = raw_input("Enter a Wikipedia URL to start from (form: '/wiki/BAND_ARTICLE': ")

	print(url)
	
	# get the root
	root = getSingleAct(wikipediaRoot, url)

	# error
	if root is None:
		print('error: unable to find root at: ' + url)
		sys.exit(-1)

	buildAndOutputGraph(root, wikipediaRoot, filename, countLimit, backupResolution)


if  __name__ =='__main__':main()

