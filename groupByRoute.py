from os import listdir
from os.path import isfile, join
import csv
import json

root = "/home/alexandra/Desktop/Visualization/rutas_bgp/csv"
routers = []

for file in listdir(root):
	i = 0
	print(file)
	file_csv = "GroupByRoute/" + file.split(".")[0] + ".csv"
	file_csv_open = open(join(root,file_csv),"w")
	if isfile(join(root,file)):
		file_open = open(join(root,file),"r+")
		reader = csv.reader(file_open, delimiter = ',')
		for row in reader:
			#ips[row[0]] = row[0]
			route = []
			for index in range(1,len(row)):
				route.append(row[index])
			if route not in routers:
				vector_line = [row[0]]
				for index in range(0,len(route)):
					vector_line.append(route[index])
				routers.append(route)
				writer = csv.writer(file_csv_open, delimiter = ',')
				writer.writerow(vector_line)
			print(i)
			i += 1
		print(len(routers))
		break

