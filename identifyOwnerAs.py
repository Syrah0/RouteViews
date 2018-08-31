from os import listdir
from os.path import isfile, join
import csv
import json

root_as = "/home/alexandra/Desktop/Visualization/rutas_bgp/csv/ASes"
root_db = "/home/alexandra/Desktop/Visualization/GeoLite2-ASN-CSV_20180821"
ases_db = {}

if isfile(join(root_db,"GeoLite2-ASN-Blocks-IPv4.csv")):
	file_open = open(join(root_db,"GeoLite2-ASN-Blocks-IPv4.csv"),"r+")
	reader = csv.reader(file_open, delimiter = ',')
	next(reader)
	for row in reader:
		try:
			new_row = row[2].split('"')[1]
			ases_db[row[1]] = new_row
		except:
			ases_db[row[1]] = row[2]

'''
file_csv_open = open(join(root_as, "ownerAS.csv"), "w")
writer = csv.writer(file_csv_open, delimiter = ',')

if isfile(join(root_as,"ASes.txt")):
	file_open = open(join(root_as,"ASes.txt"),"r+")
	reader = file_open.readlines()
	for row in reader:
		try:
			owner = ases_db[row[2:-1]]
			new_as_row = [row[2:-1]]
			new_as_row.append(owner)
			writer.writerow(new_as_row)
		except:
			pass

print("finish")
'''

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
				try:
					new_as = ases_db[row[index]]
				except:
					new_as = row[index]
				routers[row[index]] = new_as
		break

group = 0;
for router in routers.keys():
	node = {'id': routers[router], 'label': 1, 'group': group}
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
				link = {'source': routers[row[index]], 'target': routers[row[index+1]]}
				links_data.append(link)
			#	link_str = routers[row[index]] + "-" + routers[row[index+1]]
			#	links_dict[link_str] = link
			link = {'source': routers[row[len(row)-1]], 'target': row[0]}
			#link_str = routers[row[len(row)-1]] + "-" + row[0]
			#links_dict[link_str] = link
			links_data.append(link)
		break

#for link in links_dict.keys():
#	links_data.append(links_dict[link])

data = {'nodes': nodes_data, 'links': links_data}
json_name = "Graph4.json"
with open(json_name, 'w') as json_file:
	json.dump(data,json_file)

print("listo")

