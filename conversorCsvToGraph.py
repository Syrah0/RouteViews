# nodes -> Hacer diccionario de todos los AS disponibles y los IP.
# ver todos los links! (source - target)

# Leer todos los archivos y crear dos diccionarios

from os import listdir
from os.path import isfile, join
import csv
import json

root = "/home/alexandra/Desktop/Visualization/rutas_bgp/csv/GroupByRoute"
routers = {}
ips = {}
nodes_data  = []
links_data = []
links_dict = {}

for file in listdir(root):
	print(file)
	if isfile(join(root,file)):
		file_open = open(join(root,file),"r+")
		reader = csv.reader(file_open, delimiter = ',')
		for row in reader:
			ips[row[0]] = row[0]
			for index in range(1,len(row)):
				routers[row[index]] = row[index]
		break

group = 0;
for router in routers.keys():
	node = {'id': router, 'label': 1, 'group': group}
	nodes_data.append(node)
	group += 1

group = 0;
for ips in ips.keys():
	node = {'id': ips, 'label': 2, 'group': group}
	nodes_data.append(node)
	group += 1


for file in listdir(root):
	print(file)
	if isfile(join(root,file)):
		file_open = open(join(root,file),"r+")
		reader = csv.reader(file_open, delimiter = ',')
		for row in reader:
			for index in range(1,len(row)-1):
				link = {'source': row[index], 'target': row[index+1]}
			#	links_data.append(link)
				link_str = row[index] + "-" + row[index+1]
				links_dict[link_str] = link
			link = {'source': row[len(row)-1], 'target': row[0]}
			link_str = row[len(row)-1] + "-" + row[0]
			links_dict[link_str] = link
			#links_data.append(link)
		break

for link in links_dict.keys():
	links_data.append(links_dict[link])

data = {'nodes': nodes_data, 'links': links_data}
json_name = "Graph3.json"
with open(json_name, 'w') as json_file:
	json.dump(data,json_file)

print("listo")
